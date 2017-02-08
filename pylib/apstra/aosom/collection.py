# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import json

from apstra.aosom.collection_item import CollectionItem
from apstra.aosom.collection_mapper import CollectionMapper
from apstra.aosom.exc import SessionRqstError, AccessValueError, NoExistsError

__all__ = [
    'Collection',
    'CollectionItem'
]


# #############################################################################
# #############################################################################
#
#                                 Collection
#
# #############################################################################
# #############################################################################

class Collection(object):
    """
    The :class:`Collection` is used to manage a group of similar items.  This is the base
    class for all of these types of managed objects.

    The the public instance attributes and properties are:
        * :data:`api`: an instance to the :data:`Session.Api`
        * :data:`url` (str): the complete API URL for this collection
        * :data:`names` (list): the list of known item names in the collection
        * :data:`cache` (list of dict): the list of known items with each item data dictionary

    You can obtain a specific item in the collection, one that exists, or for the purposes
    of creating a new one.  The following is an example using the IpPools collection

        # >>> aos.IpPools.names
        [u'Servers-IpAddrs', u'Switches-IpAddrs']

    Obtain a specific instance and look at the value:

        # >>> my_pool = aos.IpPools['Switches-IpAddrs']
        # >>> my_pool.exists
        True
        # >>> my_pool.value
        {u'status': u'in_use', u'subnets': [{u'status': u'pool_element_in_use', u'network': u'172.20.0.0/16'}],
        u'display_name': u'Switches-IpAddrs', u'tags': [], u'created_at': u'2016-11-06T15:31:25.577510Z',
        u'last_modified_at': u'2016-11-06T15:31:25.577510Z', u'id': u'0dab20d9-ff50-4808-93ee-350a5f1af1cb'}

    You can check to see if an item exists in the collection using the `contains` operator.  For example:
        # >>> 'my-pool' in aos.IpPools
        False
        # >>> 'Servers-IpAddrs' in aos.IpPools
        True

    You can iterate through each item in the collection.  The iterable item is a class instance
    of the collection Item.  For example, iterating through the IpPools, you can look at the
    the assigned subnets field:

        # >>> for pool in aos.IpPools:
        ...    print pool.name
        ...    print pool.value['subnets']
        ...
        Servers-IpAddrs
        [{u'status': u'pool_element_in_use', u'network': u'172.21.0.0/16'}]
        Switches-IpAddrs
        [{u'status': u'pool_element_in_use', u'network': u'172.20.0.0/16'}]
    """
    URI = None

    #: :data:`LABEL` class value identifies the API property associated with the user-defined name.  Not
    #: all items use the same API property.

    LABEL = 'display_name'

    #: :data:`UNIQUE_ID` class value identifies the API property associated with the AOS unique ID.  Not
    #: all items use the same API property.

    UNIQUE_ID = 'id'

    #: Item identifies the class used for each instance within this collection.  All derived classes
    #: will use the :class:`CollectionItem` as a base class.

    Item = CollectionItem

    class ItemIter(object):
        def __init__(self, parent):
            self._parent = parent
            self._iter = iter(self._parent.names)

        def next(self):
            return self._parent[next(self._iter)]

    def __init__(self, owner):
        self.api = owner.api
        self.url = "{api}/{uri}".format(api=owner.url, uri=self.__class__.URI)
        self._cache = {}
        self.mapper = CollectionMapper(collection=self)

    # =========================================================================
    #
    #                             PROPERTIES
    #
    # =========================================================================

    @property
    def names(self):
        """
        Returns:
            A list of all item names in the current cache
        """
        if not self._cache:
            self.digest()

        return self._cache['names']

    @property
    def cache(self):
        """
        This property returns the collection digest.  If collection does not have a cached
        digest, then the :func:`digest` is called to create the cache.

        Returns:
            The collection digest current in cache
        """
        if not self._cache:
            self.digest()

        return self._cache

    # =========================================================================
    #
    #                             PUBLIC METHODS
    #
    # =========================================================================

    def digest(self):
        """
        This method retrieves information about all known items within this collection.  A cache
        is then formed that provides an index by AOS unique ID, and another by user-defined
        item name.

        Returns: a list of all known items; each item is the dictionary of item data.
        """
        got = self.api.requests.get(self.url)
        if not got.ok:
            raise SessionRqstError(resp=got)

        body = got.json()

        self._cache.clear()
        self._cache['list'] = list()
        self._cache['names'] = list()
        self._cache['by_%s' % self.LABEL] = dict()
        self._cache['by_%s' % self.UNIQUE_ID] = dict()

        items = body['items']
        for item in items:
            self._add_item(item)

        return self._cache['by_%s' % self.LABEL]

    def find(self, label=None, uid=None):
        """
        Method used to find an item in the collection by either the
        User defined value (`label`) or the AOS unique-ID generated value (`uid`)

        Args:
            label (str): the item label value, i.e. what the User sees
            uid (str): the internal unique ID value, i.e. what AOS defined

        Returns:
            - (obj) instance of the CollectionItem
            - None if item not found

        Raises:
            - AccessValueError: invalid use of arguments
        """
        if not self._cache:
            self.digest()

        if not any([label, uid]):
            raise AccessValueError('Either `label` or `id` must be provide')

        if all([label, uid]):
            raise AccessValueError('Only one of `label` or `id` can be provided')

        by_method = 'by_%s' % (self.LABEL if label else self.UNIQUE_ID)
        as_dict = self._cache[by_method].get(label or uid)

        # return None if not found
        if not as_dict:
            return None

        # return CollectionItem of this data; if the `label` was provided
        # then it's a simple index, otherwise we need to get the label value
        # out of the dict data found.

        return self[label] if label else self[as_dict[self.LABEL]]

    # =========================================================================
    #
    #                             PRIVATE METHODS
    #
    # =========================================================================

    def _add_item(self, item):
        """
        Add a new item to the collection.

        Args:
            item (dict): the datum of the actual item.

        """
        item_name = item[self.LABEL]
        item_id = item[self.UNIQUE_ID]
        self._cache['list'].append(item)
        self._cache['names'].append(item_name)
        self._cache['by_%s' % self.LABEL][item_name] = item
        self._cache['by_%s' % self.UNIQUE_ID][item_id] = item

    def _remove_item(self, item):
        """
        Removes an item from the collection

        Args:
            item (dict): the datum of the actual item

        Raises:
            RuntimeError - if item does not exist in the collection
        """
        item_name = item[self.LABEL]
        item_id = item[self.UNIQUE_ID]

        try:
            idx = next(i for i, li in enumerate(self._cache['list']) if li[self.LABEL] == item_name)
            del self._cache['list'][idx]
        except StopIteration:
            raise NoExistsError('attempting to delete item name (%s) not found' % item_name)

        idx = self._cache['names'].index(item_name)
        del self._cache['names'][idx]

        del self._cache['by_%s' % self.LABEL][item_name]
        del self._cache['by_%s' % self.UNIQUE_ID][item_id]

    # =========================================================================
    #
    #                             OPERATORS
    #
    # =========================================================================

    def __contains__(self, item_name):
        if not self._cache:
            self.digest()

        return bool(item_name in self._cache.get('names'))

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        return self.Item(collection=self, name=item_name,
                         datum=self._cache['by_%s' % self.LABEL].get(item_name))

    def __iter__(self):
        if not self._cache:
            self.digest()

        return self.ItemIter(self)

    def __iadd__(self, other):
        if not self._cache:
            self.digest()

        if not isinstance(other, CollectionItem):
            raise AccessValueError(
                "attempting to add item type(%s) not CollectionItem" % str(type(other)))

        self._add_item(other.value)
        return self

    def __isub__(self, other):
        if not self._cache:
            self.digest()

        if not isinstance(other, CollectionItem):
            raise AccessValueError(
                "attempting to remove item type(%s) not CollectionItem" % str(type(other)))

        self._remove_item(other.value)
        return self

    def __str__(self):
        return json.dumps({
            'url': self.URI,
            'by_label': self.LABEL,
            'by_id': self.UNIQUE_ID,
            'item-names': self.names
        }, indent=3)

    __repr__ = __str__
