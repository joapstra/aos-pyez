# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import importlib

from apstra.aosom.exc import SessionError

__all__ = [
    'DynamicModuleOwner'
]


class TypeDynamicModuleCatalog(type):

    def __new__(mcs, clsname, supers, clsdict):
        if 'DYNMODULEDIR' in clsdict:
            dmdir = clsdict['DYNMODULEDIR']

            clsdict['_aos_dynamic_module_'] = importlib.import_module(
                "%s.catalog" % dmdir, package=__package__)

            catmod = getattr(clsdict['_aos_dynamic_module_'], 'AosModuleCatalog')
            clsdict['_aos_dynamic_catalog_'] = catmod
            clsdict['ModuleCatalog'] = catmod.keys()

        return type.__new__(mcs, clsname, supers, clsdict)


class DynamicModuleOwner(object):
    __metaclass__ = TypeDynamicModuleCatalog

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         DYNAMIC MODULE LOADER
    # ###
    # ### ---------------------------------------------------------------------

    def __getattr__(self, amod_name):
        amod_file = self._aos_dynamic_catalog_.get(amod_name)
        if not amod_file:
            raise SessionError(message='request for unknown module: %s' % amod_name)

        got = importlib.import_module("%s.%s" % (self.DYNMODULEDIR, amod_file),
                                      package=__package__)

        cls = getattr(got, got.__all__[0])

        setattr(self, amod_name, cls(owner=self))
        return getattr(self, amod_name)
