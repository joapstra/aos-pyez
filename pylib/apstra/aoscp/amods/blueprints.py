import requests
from operator import itemgetter

from apstra.aoscp.collection import Collection, CollectionItem
from apstra.aoscp.exc import SessionRqstError

__all__ = ['Blueprints']


class BlueprintItemParamsItem(object):
    def __init__(self, blueprint, name, datum):
        self.api = blueprint.api
        self.blueprint = blueprint
        self.name = name
        self._param = {
            'info': datum,
            'value': None
        }

    @property
    def info(self):
        return self._param.get('info')

    @property
    def url(self):
        return "%s/slots/%s" % (self.blueprint.url, self.name)

    @property
    def value(self):
        return self._param.get('value') or self.get_value()

    @value.setter
    def value(self, replace_value):
        got = requests.put(self.url, headers=self.api.headers, json=replace_value)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to clear slot: %s' % self.name)

        self._param['value'] = replace_value

    def get_value(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got,
                                   message='unable to get value on slot: %s' % self.name)

        self._param['value'] = got.json()
        return self._param['value']

    def clear_value(self):
        self.value = {}


class BlueprintItemParamsCollection(object):
    Item = BlueprintItemParamsItem

    def __init__(self, parent):
        self.api = parent.api
        self.blueprint = parent
        self._slots = None
        self._cache = {}

    @property
    def names(self):
        if not self._cache:
            self.digest()

        return self._cache['names']

    def digest(self):
        got = requests.get("%s/slots" % self.blueprint.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got, message="error fetching slots")

        get_name = itemgetter('name')
        self._cache['list'] = got.json()
        self._cache['names'] = map(get_name, self._cache['list'])
        self._cache['by_name'] = {get_name(i): i for i in self._cache['list']}

    def __contains__(self, item_name):
        return bool(item_name in self._cache.get('names'))

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        # we want a KeyError to raise if the caller provides an unknown item_name
        return self.Item(self.blueprint, item_name, self._cache['by_name'][item_name])





class BlueprintCollectionItem(CollectionItem):

    def __init__(self, parent, datum):
        super(BlueprintCollectionItem, self).__init__(parent, datum)
        self.params = BlueprintItemParamsCollection(self)

    def __repr__(self):
        return str(self.datum)


class Blueprints(Collection):
    RESOURCE_URI = 'blueprints'

    class Item(BlueprintCollectionItem):
        pass
