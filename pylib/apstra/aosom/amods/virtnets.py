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
    'VirtualNetworks'
]


class VirtualNetworkItem(CollectionItem):
    def __init__(self, *vargs, **kwargs):
        super(VirtualNetworkItem, self).__init__(*vargs, **kwargs)


class VirtualNetworks(Collection):
    RESOURCE_URI = 'virtual-networks'
    Item = VirtualNetworkItem

    def __init__(self, blueprint):
        super(VirtualNetworks, self).__init__(blueprint.api)
        self.url = "{api}/{uri}".format(
            api=blueprint.url,
            uri=self.__class__.RESOURCE_URI)
