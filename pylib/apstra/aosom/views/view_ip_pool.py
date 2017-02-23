# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import jmespath
from lollipop import types as lt
from apstra.aosom.views.handler import FileView, ApiView, ViewBroker
from apstra.aosom.schemas import ip_pool as schema

__all__ = ['IpPoolView']


class _ApiView(ApiView):
    Schema = schema.IpPool

    _jpc_subnets = jmespath.compile('subnets[].{network: @}')

    @property
    def display_name(self):
        return self.import_item['name']

    @property
    def subnets(self):
        return self._jpc_subnets.search(self.import_item)


class _FileView(FileView):
    Schema = lt.Object({
        'name': lt.String(),
        'subnets': lt.List(lt.String())})

    _jpc_subnets = jmespath.compile('subnets[].network')

    @property
    def name(self):
        return self.import_item['display_name']

    @property
    def subnets(self):
        return self._jpc_subnets.search(self.import_item)


IpPoolView = ViewBroker(
    'IpPoolView',
    file_view=_FileView, api_view=_ApiView)
