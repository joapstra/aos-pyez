import requests
import json
from operator import itemgetter
from copy import copy

import retrying

from apstra.aoscp.collection import Collection, CollectionItem, CollectionValueTransformer
from apstra.aoscp.exc import SessionRqstError, SessionError

__all__ = [
    'Blueprints',
    'BlueprintParamValueTransformer'
]


class BlueprintItemParamsItem(object):
    Transformer = CollectionValueTransformer

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

    # #### ----------------------------------------------------------
    # ####   PROPERTY: value [read, write, delete]
    # #### ----------------------------------------------------------

    @property
    def value(self):
        return self._param.get('value') or self.read()

    @value.setter
    def value(self, replace_value):
        self.write(replace_value)

    @value.deleter
    def value(self):
        self.clear()

    # #### ----------------------------------------------------------
    # ####
    # ####                   PUBLIC METHODS
    # ####
    # #### ----------------------------------------------------------

    def write(self, replace_value):
        got = requests.put(self.url, headers=self.api.headers, json=replace_value)
        if not got.ok:
            raise SessionRqstError(
                message='unable to write slot: %s' % self.name,
                resp=got)

        self._param['value'] = replace_value

    def read(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get value on slot: %s' % self.name)

        self._param['value'] = copy(got.json())
        return self._param['value']

    def clear(self):
        self.write({})

    def __str__(self):
        return json.dumps({
            'Blueprint Name': self.blueprint.name,
            'Blueprint ID': self.blueprint.id,
            'Parameter Name': self.name,
            'Parameter Info': self.info,
            'Parameter Value': self.value}, indent=3)


class BlueprintItemParamsCollection(object):
    Item = BlueprintItemParamsItem

    class ItemIter(object):
        def __init__(self, params):
            self._params = params
            self._iter = iter(self._params.names)

        def next(self):
            return self._params[next(self._iter)]

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

    def __iter__(self):
        return self.ItemIter(self)


class BlueprintCollectionItem(CollectionItem):

    def __init__(self, *vargs, **kwargs):
        super(BlueprintCollectionItem, self).__init__(*vargs, **kwargs)
        self.params = BlueprintItemParamsCollection(self)

    @property
    def contents(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                message='unable to get blueprint contents',
                resp=got,
                blueprint=self)

        return got.json()

    def create(self, design_template_id, blocking=True):

        data = dict(
            display_name=self.name,
            template_id=design_template_id,
            reference_architecture="two_stage_l3clos")

        super(BlueprintCollectionItem, self).create(data)

        if not blocking:
            return True

        @retrying.retry(wait_fixed=1000, stop_max_delay=10000)
        def wait_for_id():
            return self.contents


class Blueprints(Collection):
    RESOURCE_URI = 'blueprints'
    Item = BlueprintCollectionItem
