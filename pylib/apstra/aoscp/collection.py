from operator import itemgetter
from copy import copy
import json

import requests

from apstra.aoscp.exc import SessionError, SessionRqstError, AccessValueError

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
    def id(self):
        return self.datum.get(self._parent.UNIQUE_ID)

    def write(self):
        if self.exists:
            raise NotImplementedError()

        got = requests.post(self._parent.url, headers=self.api.headers,
                            json=self.datum)

        if not got.ok:
            raise SessionRqstError(resp=got)

        # if OK, then the 'id' value is returned; update the datum
        body = got.json()
        self.datum[self._parent.UNIQUE_ID] = body[self._parent.UNIQUE_ID]

        return True

    def read(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get item name: %s' % self.name)

        self.datum = copy(got.json())
        return self.datum

    def create(self, datum):
        if self.exists:
            raise SessionError(message='cannot create, already exists')

        self.datum = copy(datum)
        return self.write()


    def __str__(self):
        return json.dumps({
            'name': self.name,
            'id': self.id,
            'datum': self.datum
        }, indent=3)


class Collection(object):
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
        if not self._cache:
            self.digest()
        return self._cache['names']

    @property
    def cache(self):
        if not self._cache:
            self.digest()

        return self._cache

    def digest(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got)

        get_name = itemgetter(self.DISPLAY_NAME)
        get_id = itemgetter(self.UNIQUE_ID)

        self._cache['list'] = got.json()
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
