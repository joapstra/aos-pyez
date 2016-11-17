# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import requests
import json
from operator import itemgetter
from copy import copy

import retrying
import semantic_version

from apstra.aosom.collection import Collection, CollectionItem, CollectionValueTransformer
from apstra.aosom.exc import SessionRqstError

__all__ = [
    'Blueprints'
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


class BlueprintCollectionItem(CollectionItem):
    """
    This class provides :class:`Blueprint` item instance management.
    """

    def __init__(self, *vargs, **kwargs):
        super(BlueprintCollectionItem, self).__init__(*vargs, **kwargs)
        self.params = BlueprintItemParamsCollection(self)

    # =========================================================================
    #
    #                             PROPERTIES
    #
    # =========================================================================

    # -------------------------------------------------------------------------
    # PROPERTY: contents
    # -------------------------------------------------------------------------

    @property
    def contents(self):
        """
        Property accessor to blueprint contents.

        :getter: returns the current blueprint data :class:`dict`
        :deletter: removes the blueprint from AOS-server

        Raises:
            SessionRqstError: upon issue with HTTP requests

        """
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                message='unable to get blueprint contents',
                resp=got)

        return got.json()

    @contents.deleter
    def contents(self):
        """
        When the `del` operation is applied to this property, then this
        action will attempt to delete the blueprint from AOS-server.  For
        example:

        >>> del my_blueprint.contents

        Raises:
            SessionRqstError: upon issue with HTTP DELETE request
        """
        got = requests.delete(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                message='unable to delete blueprint: %s' % got.reason,
                resp=got)

    # -------------------------------------------------------------------------
    # PROPERTY: build_errors
    # -------------------------------------------------------------------------

    @property
    def build_errors(self):
        """
        Property accessor to any existing blueprint build errors.

        Raises:
            SessionReqstError: upon error with obtaining the blueprint contents

        Returns:
            - either the `dict` of existing errors within the blueprint contents
            - `None` if no errors
        """
        return self.contents.get('errors')

    # =========================================================================
    #
    #                             PUBLIC METHODS
    #
    # =========================================================================

    def create(self, design_template_id, reference_arch, blocking=True):
        data = dict(
            display_name=self.name,
            template_id=design_template_id,
            reference_architecture=reference_arch)

        super(BlueprintCollectionItem, self).create(data)

        if not blocking:
            return True

        @retrying.retry(wait_fixed=1000, stop_max_delay=10000)
        def wait_for_blueprint():
            # TODO - fix this
            if not self._parent.find(key=self.name, method=self._parent.DISPLAY_NAME):
                self._parent.digest()
                assert False

        try:
            wait_for_blueprint()
        except:
            return False

        return True

    def await_build_ready(self, timeout=5000):
        """
        Wait a specific amount of `timeout` for the blueprint build status
        to return no errors.  The waiting polling interval is fixed at 1sec.

        Args:
            timeout (int): timeout to wait in miliseconds

        Returns:
            True: when the blueprint contains to build errors
            False: when the blueprint contains build errors, even after waiting `timeout`

        """
        @retrying.retry(wait_fixed=1000, stop_max_delay=timeout)
        def wait_for_no_errors():
            assert not self.build_errors

        try:
            wait_for_no_errors()
        except:
            return False

        return True


class Blueprints(Collection):
    """
    Blueprints collection class provides management of AOS blueprint instances.
    """
    RESOURCE_URI = 'blueprints'
    Item = BlueprintCollectionItem
