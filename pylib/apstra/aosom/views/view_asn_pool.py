# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import jmespath
from lollipop import types as lt
from apstra.aosom.views.handler import FileView, ApiView, ViewBroker
from apstra.aosom.schemas import asn_pool as schema


__all__ = ['AsnPoolView']


class _ApiView(ApiView):
    Schema = schema.AsnPool

    _jpc_ranges = jmespath.compile('ranges[*].{first: @[0], last: @[1]}')

    @property
    def display_name(self):
        return self.import_item['name']

    @property
    def ranges(self):
        return self._jpc_ranges.search(self.import_item)


class _FileView(FileView):
    Schema = lt.Object({
        'name': lt.String(),
        'ranges': lt.List(
            lt.List(lt.Integer()))
    })

    _jpc_ranges = jmespath.compile('ranges[*].[first, last]')

    @property
    def name(self):
        return self.import_item['display_name']

    @property
    def ranges(self):
        return self._jpc_ranges.search(self.import_item)


class AsnPoolView(ViewBroker):
    Api = _ApiView
    File = _FileView
