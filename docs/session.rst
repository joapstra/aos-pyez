.. _session:

==============
Client Session
==============

.. currentmodule:: apstra.aosom

This guide explains how you can make a connection to the AOS-server and using the elements of the Session.

Creating a Session
------------------
The first step is creating a client Session to the AOS-Server: ::

    >>> from apstra.aosom.session import Session
    >>> aos = Session('192.168.59.250', user='admin', passwd='admin)
    >>> aos.login()

The first parameter is the AOS-server IP address or hostname.  The remaining key/value arguments are documented in
the API reference section.  The user and passwd both default to `admin` if not provided.

The `login()` method will make the request to authenticate a login and provide back a session token.  If for any
reason the login attempt fails, an exception will be raised.  See :meth:`session.Session.login` for
details.  You can verify the login session information by examining the :attr:`Session.session`.

The value of the `aos.session` value looks like: ::

    >>> aos.session
    {'port': 8888,
     'server': 'aos-server',
     'token': u'eyJhbGci<~snip~>MTUiMP0skQ'}

Making use of a Session
-----------------------
The general use of the Session an interface to the exposed API features, such as the Device-Manager, using resources,
design elements, and managing network services.  You can see a list of the existing API features exposed via the
aos-pyez library by examining the `Session.ModuleCatalog` data: ::

    ['Blueprints', 'IpPools', 'DesignTemplates', 'ExternalRouters',
     'AsnPools', 'RackTypes', 'LogicalDevices', 'Devices', 'LogicalDeviceMaps']

To access any of these features, you simple use the name of the module as an attribute of the Session.  For example,
to show a list of IP Pool names managed by AOS, you would do the following: ::

    >>> aos.IpPools.names
    [u'Switches-IpAddrs', u'Servers-IpAddrs']

The modules are generally managed as a :class:`collection.Collection` and you can manage an item within a collection
as a :class:`collection.CollectionItem`.  The use of Collections and CollectionItems will be covered on separate
guide pages.

Resuming an Existing Session
----------------------------
In some cases, you may want to *pass around* the session information between programs.  Do do this you can use the
:attr:`Session.session` property.  For example returning the session as JSON data:

.. code-block:: python
    :caption: save-session.py

    >>> keep_session = aos.session
    >>> json.dump(keep_session, open('keep_session.json', 'w+'), indent=2)

And then in a different program, you can use this session data to restore a connection:

.. code-block:: python
    :caption: restore-session.py

    >>> aos = Session()
    >>> had_session = json.load(open('keep_session.json'))
    >>> aos.session = had_session

And now the session is again active.  If the session could not be restored for any reason, then an exceptions will
be raised.  See the :meth:`Session.session.login` for details on those exceptions.

.. _session_requests:

Session.api.requests
--------------------
The Session instance maintains properties that allows you direct `Requests
<http://docs.python-requests.org/en/latest/>`_ level access, should you need it for
any reason.  For example, you may want access to API capabilities not presently exposed by the aos-pyez library.
You can use the :attr:`Session.api` and :attr:`Session.api.requests` values.  The :attr:`api.url` maintains the top
level HTTP URL to the AOS-Server: ::

    >>> aos.api.url
    'http://aos-server:8888/api'

And the :attr:`api.requests` is a `Requests Session <http://docs.python-requests
.org/en/latest/user/advanced/#session-objects>`_ object used for direct access. Here is an example of directly
invoking a GET on API version build information: ::

    >>> aos.api.requests.get("%s/versions/build" % aos.api.url)
    <Response [200]>

And the data returned by using the :attr:`api.requests` is the same Requests Response object: ::

    >>> got = aos.api.requests.get("%s/versions/build" % aos.api.url)
    >>> got.json()
    {u'version': u'1.1.0-11', u'build_datetime': u'2016-12-12_16:46:51_PST'}

The :attr:`Session.api.requests` property stores the necessary headers from the login authentication.  This
means that you do not need to explicitly provide the `headers=` value on the requests call.  For example, doing a GET
on the IP Pools would require an authentication token.  Here is how you could directly invoke the requests library
to do the same data retrieval as shown before, in this case getting the raw JSON output.

.. code-block:: python
   :linenos:

    # each collection has a url property as well!
    >>> aos.IpPools.url
    'http://aos-server:8888/api/resources/ip-pools'

    >>> got = aos.api.requests.get(aos.IpPools.url)
    >>> print json.dumps(got.json(), indent=2)
    {
      "items": [
        {
          "status": "in_use",
          "subnets": [
            {
              "status": "pool_element_in_use",
              "network": "172.20.0.0/16"
            }
          ],
          "display_name": "Switches-IpAddrs",
          "tags": [],
          "created_at": "2017-01-28T19:57:12.887618Z",
          "last_modified_at": "2017-01-28T19:57:12.887618Z",
          "id": "65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0"
        },
        {
          "status": "in_use",
          "subnets": [
            {
              "status": "pool_element_in_use",
              "network": "172.21.0.0/16"
            }
          ],
          "display_name": "Servers-IpAddrs",
          "tags": [],
          "created_at": "2017-01-28T19:57:13.096657Z",
          "last_modified_at": "2017-01-28T19:57:13.096657Z",
          "id": "0310d821-d075-4075-bdda-55cc6df57258"
        }
      ]
    }
