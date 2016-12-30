# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import json
import requests
import semantic_version

from apstra.aosom.exc import SessionRqstError, AccessValueError
from apstra.aosom.collection_item import CollectionItem

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

        >>> aos.IpPools.names
        [u'Servers-IpAddrs', u'Switches-IpAddrs']

    Obtain a specific instance and look at the value:

        >>> my_pool = aos.IpPools['Switches-IpAddrs']
        >>> my_pool.exists
        True
        >>> my_pool.value
        {u'status': u'in_use', u'subnets': [{u'status': u'pool_element_in_use', u'network': u'172.20.0.0/16'}],
        u'display_name': u'Switches-IpAddrs', u'tags': [], u'created_at': u'2016-11-06T15:31:25.577510Z',
        u'last_modified_at': u'2016-11-06T15:31:25.577510Z', u'id': u'0dab20d9-ff50-4808-93ee-350a5f1af1cb'}

    You can check to see if an item exists in the collection using the `contains` operator.  For example:
        >>> 'my-pool' in aos.IpPools
        False
        >>> 'Servers-IpAddrs' in aos.IpPools
        True

    You can iterate through each item in the collection.  The iterable item is a class instance
    of the collection Item.  For example, iterating through the IpPools, you can look at the
    the assigned subnets field:

        >>> for pool in aos.IpPools:
        ...    print pool.name
        ...    print pool.value['subnets']
        ...
        Servers-IpAddrs
        [{u'status': u'pool_element_in_use', u'network': u'172.21.0.0/16'}]
        Switches-IpAddrs
        [{u'status': u'pool_element_in_use', u'network': u'172.20.0.0/16'}]
    """
    RESOURCE_URI = None

    #: :data:`DISPLAY_NAME` class value identifies the API property associated with the user-defined name.  Not
    #: all items use the same API property.

    DISPLAY_NAME = 'display_name'

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
        self.url = "{api}/{uri}".format(api=owner.url, uri=self.__class__.RESOURCE_URI)
        self._cache = {}

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
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got)

        body = got.json()
        aos_1_0 = semantic_version.Version('1.0', partial=True)

        self._cache.clear()
        self._cache['list'] = list()
        self._cache['names'] = list()
        self._cache['by_%s' % self.DISPLAY_NAME] = dict()
        self._cache['by_%s' % self.UNIQUE_ID] = dict()

        items = body['items'] if self.api.version['semantic'] > aos_1_0 else body
        for item in items:
            self._add_item(item)

        return self._cache['by_%s' % self.DISPLAY_NAME]

    def find(self, key, method):
        """
        Used to find a specific item identified by `key` within the collection.  The caller can use
        either the "name" method or the "id" method.

        For example, the following will find an IpPool by user display-name:

        >>> aos.IpPools.find(method='display_name', key='Servers-IpAddrs')
        {u'status': u'in_use', u'subnets': [{u'status': u'pool_element_in_use',
        u'network': u'172.21.0.0/16'}], u'display_name': u'Servers-IpAddrs', u'tags': [],
        u'created_at': u'2016-11-06T15:31:25.858930Z', u'last_modified_at': u'2016-11-06T15:31:25.858930Z',
        u'id': u'08965710-1d37-4658-81cb-3a54bb6ef626'}

        And the following will find the same IpPools using the AOS unique ID vlaue:

        >>> aos.IpPools.find(method='id', key='08965710-1d37-4658-81cb-3a54bb6ef626')
        {u'status': u'in_use', u'subnets': [{u'status': u'pool_element_in_use',
        u'network': u'172.21.0.0/16'}], u'display_name': u'Servers-IpAddrs', u'tags': [],
        u'created_at': u'2016-11-06T15:31:25.858930Z', u'last_modified_at': u'2016-11-06T15:31:25.858930Z',
        u'id': u'08965710-1d37-4658-81cb-3a54bb6ef626'}

        Args:
            key (str): the value that identifies the item to find
            method (str): the method to find the item.

        Returns:
            - the specific item instance if the item is found
            - `None` if the item is not found
        """
        if not self._cache:
            self.digest()

        by_method = 'by_%s' % method
        if by_method not in self._cache:
            raise AccessValueError(message='unable to use find method: %s' % by_method)

        return self._cache[by_method].get(key)

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
        item_name = item[self.DISPLAY_NAME]
        item_id = item[self.UNIQUE_ID]
        self._cache['list'].append(item)
        self._cache['names'].append(item_name)
        self._cache['by_%s' % self.DISPLAY_NAME][item_name] = item
        self._cache['by_%s' % self.UNIQUE_ID][item_id] = item

    def _remove_item(self, item):
        """
        Removes an item from the collection

        Args:
            item (dict): the datum of the actual item

        Raises:
            RuntimeError - if item does not exist in the collection
        """
        item_name = item[self.DISPLAY_NAME]
        item_id = item[self.UNIQUE_ID]

        try:
            idx = next(i for i, li in enumerate(self._cache['list']) if li[self.DISPLAY_NAME] == item_name)
            del self._cache['list'][idx]
        except StopIteration:
            raise RuntimeError('attempting to delete item name (%s) not found' % item_name)

        idx = self._cache['names'].index(item_name)
        del self._cache['names'][idx]

        del self._cache['by_%s' % self.DISPLAY_NAME][item_name]
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
                         datum=self._cache['by_%s' % self.DISPLAY_NAME].get(item_name))

    def __iter__(self):
        if not self._cache:
            self.digest()

        return self.ItemIter(self)

    def __iadd__(self, other):
        if not isinstance(other, CollectionItem):
            raise RuntimeError("attempting to add item type(%s) not CollectionItem" % str(type(other)))

        self._add_item(other.value)
        return self

    def __isub__(self, other):
        if not isinstance(other, CollectionItem):
            raise RuntimeError(
                "attempting to remove item type(%s) not CollectionItem" % str(type(other)))

        self._remove_item(other.value)
        return self

    def __str__(self):
        return json.dumps({
            'url': self.RESOURCE_URI,
            'by_display_name': self.DISPLAY_NAME,
            'by_id': self.UNIQUE_ID,
            'item-names': self.names
        }, indent=3)

    __repr__ = __str__
