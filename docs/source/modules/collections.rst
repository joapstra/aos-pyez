Collections Overview
====================

A Collection is a way to manage a group of similar items.  The Collection class is a base-class used by many of
the other modules within the AOS-PyEZ framework.  In general, you can use a Collection to do the following:

   * Manage a specific item by the user defined item name
   * Manage a specific item by the AOS unique id value
   * Get a list of known names in the collection
   * Determine if an item exists in the collection
   * Iterate through each item in the collection

Collection
----------
:class:`Collection` is the base-class for all collections managed by the AOS-PyEZ framework.  Each of the collections
managed within the AOS-PyEZ framework will subclass, and may provide additional functionality or override
items in this base-class.

.. currentmodule:: apstra.aosom.collection

.. autoclass:: Collection
   :members:

CollectionItem
--------------
:class:`CollectionItem` is the base-class for all items that are stored within a collection.  Each of the collections
managed within the AOS-PyEZ framework will subclass, and may provide additional functionality or override
items in this base-class.

.. autoclass:: CollectionItem
   :members:

