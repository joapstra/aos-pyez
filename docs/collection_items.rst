Collection Item
===============
You can manage individual collection items in generally the same way.  This guide page provides general usage
information.  Specific aos-pyez collections may have additional information that you can review as well.
For more information about aos-pyez collections: :ref:`collections`.

Item Properties
---------------
The following are commonly used collection item properties:

    * `name` - This is the User provided name of the item, aka "label"
    * `id` - This is the AOS-Server generated unique-ID value, aka "uid"
    * `value` - This is a dict of data specific to the collection item that stores the raw data about this item.
    * `collection` - This is the parent collection instance for this item.




Create an Item
--------------
You can create a new item in one of two ways.  The first way is to access a collection using the new item name
and then issuing a :meth:`write` on the item.  The :meth:`write` will detect that this item does not currently
exist in the AOS-Server and make the proper API call to create it.  There is an explicit :meth:`create` method
that you could call in this particular use-case, but it is there for your programming convenience only.

For example, let's create a new IP Pool
called "pod-1-switch-loopbacks".  The first step is to index the IP Pools collection: ::

    >>> new_pool = aos.IpPools['pod-1-switch-loopbacks']
    >>> new_pool.exists
    False

The next step is to provide the necessary item value data for this item.  The structure / contents of the item
data is going to be specific to each type of item.  For specific item details, you will need to refer to the
AOS-Server API Reference documentation available directly from the UI page.

You cannot write directly to the item :attr:`value` property, but you can provide the contents when you do the
:meth:`write` invocation: ::

    # setup a dict of data required for the ip-pool item:
    >>> pool_data = dict(subnets=[dict(network='192.168.10.0/24')])

    # write the data, which will trigger a create
    >>> new_pool.write(pool_data)

Upon success, the new pool now exists, and has been assigned a unique ID by AOS-Server.  This information is
updated within collection and item instance for your immediate use: ::

    >>> new_pool.exists
    True
    >>> new_pool.id
    u'45de5b41-1846-4057-afe8-9f5b93f8c5a6'

If for any reason the :meth:`write` fails, an exception will be raised.  So you should generally wrap a try/except
around any operation you are doing with the aos-pyez library.  For exception details, please refer to the reference
section: :ref:`api_reference`.

Write an Item
-------------
If you need to create or update an existing collection item, you can do so using the :meth:`write` method.  If
the item does not exist in the AOS-Server, then this method will perform the necessary POST command to create it.
Otherwise, the :meth:`write` method will issue a PUT command to update-overwrite.

Read an Item
------------
Generally speaking, when you access a collection item, the item value is already present.  If you need for any reason
to retrieve the current value from the AOS-Server, you can invoke the :meth:`read` method.  This will refresh
the instance value.

Delete an Item
--------------
You can delete an item in one of two ways - either calling the :meth:`delete` method on the instance or using the
python `del` operation on the item :attr:`value` property.  ::

    #
    # delete item using the method
    #
    >>> new_pool.delete()
    #
    # equivalent to using the del operator
    #
    >>> del new_pool.value


Backup / Restore Local JSON File
--------------------------------
You may find it useful to make a copy of a collection item and store it as a JSON file on your local filesystem.  You
can then later restore this value from your local filesystem.  Each collection item provides a :meth:`jsonfile_save`
and :meth:`jsonfile_load` for backup and restore.  By default, the :meth:`jsonfile_save` will store the JSON file
in your local current working directory using the :attr:`name` property as the filename.  You can override this
default behavior with the various arguments to the :meth:`jsonfile_save` method.

.. code-block:: python

    >>> # assume new_pool was created with name='pod-1-switch-loopbacks'

    >>> new_pool.jsonfile_save()                                     # saves to 'pod-1-switch-loopbacks.json' in $CWD
    >>> new_pool.jsonfile_save(dirpath='/tmp')                       # /tmp/pod-1-switch-loopbacks.json
    >>> new_pool.jsonfile_save(dirpath='/tmp', filename='save-me')   # /tmp/save-me.json


The :meth:`jsonfile_load` method always requires a specific filepath: ::

    >>> new_pool.jsonfile_load('/tmp/pod-1-switch-loopbacks.json')

.. note::

    The :meth:`jsonfile_load` method only loads the contents of the file into the instance object.  If you are using
    this method to create a new item in the AOS-Server, you will then need to issue the :meth:`write` method

Accessing the AOS-Server API Directly
-------------------------------------
In some cases you might want to access the AOS-Server API directly.  The following properties are available should
you need to do so:

    * `url` - This is the AOS-Server specific URL for this item
    * `api` - This is the Session instance so you can access the AOS-Server API

For example, let's say you want to issue a DELETE command directly:

    >>> aos.IpPools.names
    [u'Switches-IpAddrs', u'Servers-IpAddrs', u'my_pool']
    >>>
    >>> pool = aos.IpPools['my_pool']
    >>>
    >>> pool.url
    u'http://aos-server:8888/api/resources/ip-pools/a91d088f-ee0e-4bfc-803f-9078954d5826'
    >>>
    >>> pool.api.requests.delete(pool.url)
    <Response [202]>
