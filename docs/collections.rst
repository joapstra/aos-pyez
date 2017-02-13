.. _collections:

Collections
===========

A Collection is a way to manage a group of similar items.  The Collection base-class is used by many of
the other modules within the aos-pyez library.  In general, you can use a Collection to do the following:

   * Get a list of known names in the collection
   * Determine if an item exists in the collection
   * Manage a specific item by the user defined item name (aka "label")
   * Manage a specific item by the AOS unique id value (aka "uid")
   * Iterate through each item in the collection

Collection Properties
---------------------
The following properties are commonly used:

    * `names` - provides a list of names known to the AOS-Server
    * `LABEL` - the collection item property that identifies the User name for the item
    * `UNIQUE_ID` - the collection item property that idetnifies the AOS-Server UID value



Accessing A Collection
----------------------
You can access a collection of items via the Session instance.  You can see a list of available collections from the
as described in the :ref:`session` guide page.  For example, accessing the collection of IP Pools, you would access
the `IpPools` session property: ::

    >>> ip_pools = aos.IpPools

List of Known Items in a Collection
-----------------------------------
Each collection maintains a digest of information from the AOS-Server.  This information is demand loaded when you
access the collection.  The digest contains the list of known User names ("labels") as well as some information about
each of the items.  The specific information that is collected and known is dependent on the collection.  Refer to
documentation on each of the collections for more details.  To see a list of known collection labels, you can access
the collection :attr:`names` property.  For example, the AOS-server presently knows about the following IP Pools: ::

    >>> aos.IpPools.names
    [u'Switches-IpAddrs', u'Servers-IpAddrs']

Accessing a Collection Item
---------------------------
You can access a specific collection item in one of a few ways.  The first way is by indexing the collection by the
label name.  For example, accessing the IP Pool named "Switches-IpAddrs": ::

    >>> this_pool = aos.IpPools["Switches-IpAddrs"]
    >>> this_pool.exists
    True
    >>> this_pool.id
    u'65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0'

If you attempt to access a collection item that does not exist using this method, you will still get an instance of
a collection item, but this item does not yet exist in the AOS-Server.  For example: ::

    >>> new_pool = aos.IpPools['my_new_pool']
    >>> new_pool.exists
    False
    >>> new_pool.id
    >>>  # None

Generally the above approach is used when you want to create a new instance of a collection item.  The topic of
adding and removing collection items is covered in a following section.

Finding an Item in a Collection
-------------------------------
Another way to access, or attempt to access, a collection item is using the collections :meth:`find` method.  This
will either return an item that exists, or `None`.  The :meth:`find` method allows you on of two approaches; either
find an item by its name or unqiue-id.  For example: ::

    >>> this_pool = aos.IpPools.find(label=u'Switches-IpAddrs')
    >>> this_pool.id
    >>> this_pool.id
    u'65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0'

Let's say that all you have is the UID value, perhaps from another API call, and you need to find the IP Pool
for that UID.  You can find it by using the `uid` argument, for example: ::

    >>> pool = aos.IpPools.find(uid="65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0")
    >>> pool.exists
    True
    >>> pool.name
    u'Switches-IpAddrs'

If you attempt to find an item that does not exist, by either `label` or `uid`, the :meth:`find` method will return
None.

    >>> pool = aos.IpPools.find(uid="does not exist")
    >>> pool is None
    True

Checking for Item in Collection
-------------------------------
If you simply want to determine if an item exists in the collection, i.e. known to the AOS-Server, you can use the
`in` operator.  For example, let's say you want to see if the IP Pool called "MyPool" is known to the AOS-Server:

    >>> "MyPool" in aos.IpPools
    False

This means that the AOS-Server does not manage this item.

.. warning::

    The collection will only report on items that are known to the AOS-Server.  So if you are in
    the process of creating a new collection item, but have not yet saved it to the AOS-Server, then the collection will
    still report that the item is not in the collection.

Iterating through Collection Items
----------------------------------
If you need to loop through each item in a collection, you can do this using any pythonic iteration mechanism
because the Collection base-class implements the iteration protocol.  So you can do things like this: ::

    >>> for pool in aos.IpPools:
    ...    print pool.name, pool.id
    ...
    Switches-IpAddrs 65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0
    Servers-IpAddrs 0310d821-d075-4075-bdda-55cc6df57258

Adding and Removing Collection Items
------------------------------------
The Collection base-class supports the :meth:`__iadd__` and :meth:`__isub__` operators.  This is one way you can
add and remove items.  Other methods are described in the Collection-Item guide document.

Updating Collection Digest
--------------------------
If you need to update the aos-pyez collection data from the AOS-Server, for example, you're anticipating a change
to the AOS-Server outside your program, then you can invole the collection :meth:`digest` method.  This method
will query the AOS-Server for what it knows, and rebuild the internal collection cache.

Pretty-Printing
---------------
Each collection implements the :meth:`__str__` operator so you can pretty-print information about the collection.
This is useful for interatice python sessions or general debugging.  For example, here is the output for the
IP Pools collection:

.. code-block:: python
    :linenos:

    >>> aos.IpPools
    {
       "url": "resources/ip-pools",
       "by_id": "id",
       "item-names": [
          "Switches-IpAddrs",
          "Servers-IpAddrs"
       ],
       "by_label": "display_name"
    }

Breaking down the above information:

    * line 3: this is the URL in the AOS-Server API to access this collection
    * line 4: the `id` is the actual property name within the collection item to provide the UID value
    * lines 5-8: the list of known names managed by the AOS-Server
    * line 9: the `display_name` is the actual property name within the collection item to provide the label value

Accessing the AOS-Server API Directly
-------------------------------------

The following properties are used if you need to access the AOS-Server API directly.

    * `url` - This is the AOS-Server specific URL for this collection
    * `api` - This is the Session instance so you can access the AOS-Server API

 For example, here is the way you could directly perform a GET on the IP Pools collection:

    >>> aos.IpPools.url
    'http://aos-server:8888/api/resources/ip-pools'

    >>> got = aos.IpPools.api.requests.get(aos.IpPools.url)
    >>> got
    <Response [200]>

.. note::

    You do *not* need to provide the Requests header value to the `requests.get` call because the aos-pyez
    Session api instance has these values already stored within the session instance.