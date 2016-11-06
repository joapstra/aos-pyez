from os import path
from operator import itemgetter
from copy import copy
import json

import requests
import semantic_version

from apstra.aosom.exc import SessionError, SessionRqstError, AccessValueError

__all__ = [
    'Collection',
    'CollectionItem',
    'CollectionValueTransformer',
    'CollectionValueMultiTransformer'
]


class CollectionValueTransformer(object):
    def __init__(self, collection,
                 read_given=None, read_item=None,
                 write_given=None, write_item=None):

        self.collection = collection
        self._read_given = read_given or collection.UNIQUE_ID
        self._read_item = read_item or collection.DISPLAY_NAME
        self._write_given = write_given or collection.DISPLAY_NAME
        self._write_item = write_item or collection.UNIQUE_ID

    def xf_in(self, value):
        """
        transforms the native API stored value (e.g. 'id') into something else,
        (e.g. 'display_name')
        """
        retval = {}

        def lookup(lookup_value):
            item = self.collection.find(key=lookup_value, method=self._read_given)
            if not item:
                raise AccessValueError(message='unable to find item key=%s, by=%s' %
                                               (_val, self._write_given))
            return item[self._read_item]

        for _key, _val in value.iteritems():
            if isinstance(_val, (list, dict)):
                retval[_key] = map(lookup, _val)
            else:
                retval[_key] = lookup(_val)

        return retval

    def xf_out(self, value):
        retval = {}

        def lookup(lookup_value):
            item = self.collection.find(key=lookup_value, method=self._write_given)
            if not item:
                raise AccessValueError(
                    message='unable to find item key=%s, by=%s' %
                            (_val, self._write_given))

            return item[self._write_item]

        for _key, _val in value.iteritems():
            if isinstance(_val, (list, dict)):
                retval[_key] = map(lookup, _val)
            else:
                retval[_key] = lookup(_val)

        return retval


class CollectionValueMultiTransformer(object):
    def __init__(self, session, xf_map):
        self.xfs = {
            id_name: CollectionValueTransformer(getattr(session, id_type))
            for id_name, id_type in xf_map.items()
        }

    def xf_in(self, values):
        return {
            id_name: self.xfs[id_name].xf_in({id_name: id_value})
            for id_name, id_value in values.items()
        }

    def xf_out(self, values):
        retval = {}
        for id_name, id_value in values.items():
            retval.update(self.xfs[id_name].xf_out({id_name: id_value}))
        return retval


class CollectionItem(object):
    """
    An item within a given :class:`Collection`.  The following public attributes and
    properties are available:

        * :attr:`name` - the user provided item name
        * :attr:`id` - the AOS-server unique ID value
        * :attr:`api` - the instance to the :mod:`Session.Api` instance.
        * :attr:`url` - the string URL for this instance.
        * :attr:`exists` - True if this item exists in AOS-server

    """
    def __init__(self, parent, name, datum):
        self.name = name
        self._parent = parent
        self.api = parent.api
        self.datum = datum
        self._url = None

    @property
    def url(self):
        if self._url:
            return self._url

        if not self.id:
            return None

        self._url = "%s/%s" % (self._parent.url, self.id)
        return self._url

    @property
    def exists(self):
        return bool(self.datum and self.id)

    @property
    def value(self):
        return self.datum

    @property
    def id(self):
        return self.datum.get(self._parent.UNIQUE_ID) if self.name in self._parent else None

    def write(self):
        if self.exists:
            raise NotImplementedError('cannot write to an existing object here')

        got = requests.post(self._parent.url, headers=self.api.headers,
                            json=self.datum)

        if not got.ok:
            raise SessionRqstError(
                message='unable to write: %s' % got.reason,
                resp=got)

        # if OK, then the 'id' value is returned; update the datum
        body = got.json()
        self.datum[self._parent.UNIQUE_ID] = body[self._parent.UNIQUE_ID]

        return True

    def read(self):
        """
        Retrieves the item value from the AOS-server.

        Raises:
            SessionRqstError: upon REST call error

        Returns: a copy of the item value, usually a `dict`.
        """
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get item name: %s' % self.name)

        self.datum = copy(got.json())
        return self.datum

    def create(self, **kwargs):
        if self.exists:
            raise SessionError(message='cannot create, already exists')

        self.datum = copy(kwargs['datum'])
        return self.write()

    def jsonfile_save(self, dirpath=None, filename=None, indent=3):
        """
        Saves the contents of the item to a JSON file.

        Args:
            dirpath:
                The path to the directory to store the file.  If none provided
                then the file will be stored in the current working directory

            filename:
                The name of the file, stored within the `dirpath`.  If
                not provided, then the filename will be the item name.

        Raises:
            IOError: for any I/O related error
        """
        ofpath = path.join(dirpath or '.', filename or self.name) + '.json'
        json.dump(self.value, open(ofpath, 'w+'), indent=indent)

    def jsonfile_load(self, filepath):
        """
        Loads the contents of the JSON file, `filepath`, as the item value.

        Args:
            filepath (str): complete path to JSON file

        Raises:
            IOError: for any I/O related error
        """
        self.datum = json.load(open(filepath))

    def __str__(self):
        return json.dumps({
            'name': self.name,
            'id': self.id,
            'value': self.value
        }, indent=3)


class Collection(object):
    """
    The :class:`Collection` is used to manage a group of similar items.  This is the base
    class for all of these types of managed objects.
    """
    RESOURCE_URI = None
    DISPLAY_NAME = 'display_name'
    UNIQUE_ID = 'id'

    class Item(CollectionItem):
        pass

    class ItemIter(object):
        def __init__(self, parent):
            self._parent = parent
            self._iter = iter(self._parent.names)

        def next(self):
            return self._parent[next(self._iter)]

    def __init__(self, api):
        self.api = api
        self.url = "{api}/{uri}".format(api=api.url, uri=self.__class__.RESOURCE_URI)
        self._cache = {}

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

    def digest(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got)

        get_name = itemgetter(self.DISPLAY_NAME)
        get_id = itemgetter(self.UNIQUE_ID)

        body = got.json()
        aos_1_0 = semantic_version.Version('1.0', partial=True)
        self._cache['list'] = body['items'] if self.api.version['semantic'] > aos_1_0 else body

        self._cache['names'] = map(get_name, self._cache['list'])
        self._cache['by_%s' % self.DISPLAY_NAME] = {
            get_name(n): n for n in self._cache['list']}
        self._cache['by_%s' % self.UNIQUE_ID] = {
            get_id(n): n for n in self._cache['list']}

        return self._cache['by_%s' % self.DISPLAY_NAME]

    def find(self, key, method):
        if not self._cache:
            self.digest()

        by_method = 'by_%s' % method
        if by_method not in self._cache:
            raise AccessValueError(message='unable to use find method: %s' % by_method)

        return self._cache[by_method].get(key)

    def __contains__(self, item_name):
        if not self._cache:
            self.digest()

        return bool(item_name in self._cache.get('names'))

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        return self.Item(parent=self, name=item_name,
                         datum=self._cache['by_%s' % self.DISPLAY_NAME].get(item_name))

    def __iter__(self):
        if not self._cache:
            self.digest()

        return self.ItemIter(self)
