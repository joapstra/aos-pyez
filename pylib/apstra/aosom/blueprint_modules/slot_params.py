import requests
import json
from operator import itemgetter
from copy import copy

import semantic_version

from apstra.aosom.valuexf import CollectionValueTransformer
from apstra.aosom.exc import SessionRqstError

__all__ = ['BlueprintItemParamsCollection']


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
        """
        This method writes (PUT) the given parameter value.  If you are looking
        to merge/update a value into the existing parameter, use the :meth:`update`
        instead.

        Args:
            replace_value (dict): the new parameter value; will replace anything that
             previously exists.

        Raises:
            SesssionRqstError - upon API request error
        """
        got = requests.put(self.url, headers=self.api.headers, json=replace_value)
        if not got.ok:
            raise SessionRqstError(
                message='unable to write slot: %s' % self.name,
                resp=got)

        self._param['value'] = replace_value

    def read(self):
        """
        This method will retrieve the current parameter/slot value.

        Returns:
            The value, as a dict, of the parameter.
        """
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get value on slot: %s' % self.name)

        self._param['value'] = copy(got.json())
        return self._param['value']

    def clear(self):
        """
        This method will remove any values currently stored in the parameter.  This action
        is accomplished by writing (PUT) an empty dictionary value; see the :meth:`write`
        for further details.
        """
        self.write({})

    def update(self, merge_value):
        """
        This method will issue a PATCH to the slot value so that the caller can merge the
        provided :param:`merge_value` with the existing value.  Once the PATCH completes,
        this method with then invoke :meth:`read` to retrieve the fully updated value.

        Args:
            merge_value: data value to merge with existing slot value.

        Raises:
            SessionRqstError - if error with API request
        """
        got = requests.patch(self.url, headers=self.api.headers, json=merge_value)
        if not got.ok:
            raise SessionRqstError(
                message='unable to patch slot: %s' % self.name,
                resp=got)

        self.read()

    def __str__(self):
        return json.dumps({
            'Blueprint Name': self.blueprint.name,
            'Blueprint ID': self.blueprint.id,
            'Parameter Name': self.name,
            'Parameter Info': self.info,
            'Parameter Value': self.value}, indent=3)

    __repr__ = __str__


class BlueprintItemParamsCollection(object):
    Item = BlueprintItemParamsItem

    class ItemIter(object):
        def __init__(self, params):
            self._params = params
            self._iter = iter(self._params.names)

        def next(self):
            return self._params[next(self._iter)]

    def __init__(self, owner):
        self.api = owner.api
        self.blueprint = owner
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

        body = got.json()
        aos_1_0 = semantic_version.Version('1.0', partial=True)

        self._cache['list'] = body['items'] if self.api.version['semantic'] > aos_1_0 else body
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

    def __str__(self):
        return json.dumps({
            'name': self.blueprint.name,
            'slots': self.names
        }, indent=3)

    __repr__ = __str__
