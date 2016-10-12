from operator import itemgetter

import requests
from apstra.aoscp.exc import SessionRqstError

__all__ = [
    'ResourcePool',
    'ResourcePoolItem'
]


class ResourcePoolItem(object):
    def __init__(self, pool, datum):
        self.pool = pool
        self.datum = datum

    @property
    def exists(self):
        return bool(self.datum)


class ResourcePool(object):
    RESOURCE_URI = None

    class Item(ResourcePoolItem):
        pass

    def __init__(self, api):
        self.api = api
        self.url = "{api}/{uri}".format(api=api.url, uri=self.__class__.RESOURCE_URI)
        self._cache = {}

    @property
    def names(self):
        if not self._cache:
            self.digest()
        return self._cache['names']

    def digest(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got)

        self._cache['list'] = got.json()
        get_name = itemgetter('display_name')
        self._cache['names'] = map(get_name, self._cache['list'])
        self._cache['by_name'] = {get_name(n): n for n in self._cache['list']}

        return self._cache['by_name']

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        return self.Item(self, self._cache['by_name'].get(item_name))
