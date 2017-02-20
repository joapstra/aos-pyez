# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import jmespath
from lollipop import types as lt
from apstra.aosom.views import ViewHandler

from apstra.aosom.session_modules import ip_pools as module
from apstra.aosom.schemas import ip_pool as schema

__all__ = ['IpPoolView']

# using jmespath to parse/transform data.  precompile the expressions
# that we will be using.  'a->v' means transform from AOS to View and
# 'v->a' means transform from View to AOS.  #dope

_jpc_subnets = {
    'a->v': jmespath.compile('subnets[].network'),
    'v->a': jmespath.compile('subnets[].{network: @}')
}


class IpPoolView(ViewHandler):

    Api = schema.IpPool
    Module = module.IpPools

    # -------------------------------------------------------------------------
    # AOS -> View
    # -------------------------------------------------------------------------
    # The View schema defines the structure of the content and provides
    # the functions to convert the API data to the view schema
    # -------------------------------------------------------------------------

    View = lt.Object({
        'name': lt.FunctionField(
            lt.String(),
            lambda api: api[module.IpPools.LABEL]),

        'subnets': lt.FunctionField(
            lt.List(lt.String()),
            lambda api: _jpc_subnets['a->v'].search(api))})

    # -------------------------------------------------------------------------
    # View -> AOS
    # -------------------------------------------------------------------------
    # The ViewHandler must implement the property names defined by the AOS
    # API schema.
    # -------------------------------------------------------------------------

    @property
    def display_name(self):
        return self.data['name']

    @property
    def subnets(self):
        return _jpc_subnets['v->a'].search(self.data)
