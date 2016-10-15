from operator import itemgetter

import requests
from apstra.aoscp.exc import SessionRqstError

__all__ = [
    'Collection',
    'CollectionItem'
]


class CollectionItem(object):
    def __init__(self, parent, datum):
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
        return bool(self.datum and self.name in self._parent)

    @property
    def name(self):
        return self.datum[self._parent.DISPLAY_NAME]

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

    def __repr__(self):
        return str({
            'name': self.name,
            'id': self.id,
            'datum': self.datum
        })


class Collection(object):
    RESOURCE_URI = None
    DISPLAY_NAME = 'display_name'
    UNIQUE_ID = 'id'

    class Item(CollectionItem):
        pass

    def __init__(self, api):
        self.api = api
        self.url = "{api}/{uri}".format(api=api.url, uri=self.__class__.RESOURCE_URI)
        self._cache = {}

    @property
    def names(self):
        if not self._cache:
            self.digest()
        return self._cache['by_name']

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
        self._cache['by_name'] = {get_name(n): n for n in self._cache['list']}
        self._cache['by_id'] = {get_id(n): n for n in self._cache['list']}

        return self._cache['by_name']

    def __contains__(self, item_name):
        if not self._cache:
            self.digest()

        return bool(item_name in self._cache.get('names'))

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        return self.Item(self, self._cache['by_name'].get(item_name))

    def __iter__(self):
        if not self._cache:
            self.digest()

        return self._cache['by_name'].iteritems()