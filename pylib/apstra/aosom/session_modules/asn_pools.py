# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from apstra.aosom.collection import Collection
from apstra.aosom.collection_item import CollectionItem

__all__ = ['AsnPools']


class AsnPoolItem(CollectionItem):

    @property
    def in_use(self):
        return self.value['status'] == "in_use"


class AsnPools(Collection):
    Item = AsnPoolItem
    URI = 'resources/asn-pools'
