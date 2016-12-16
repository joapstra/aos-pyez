# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from apstra.aosom.exc import AccessValueError

__all__ = [
    'CollectionValueTransformer',
    'CollectionValueMultiTransformer'
]


class CollectionValueTransformer(object):
    def __init__(self, collection,
                 read_given=None, read_item=None,
                 write_given=None, write_item=None):

        self.collection = collection
        self._read_given = read_given or collection.UNIQUE_ID
        self._read_item = read_item or collection.DISPLAY_NAME
        self._write_given = write_given or collection.DISPLAY_NAME
        self._write_item = write_item or collection.UNIQUE_ID

    def xf_in(self, value):
        """
        transforms the native API stored value (e.g. 'id') into something else,
        (e.g. 'display_name')
        """
        retval = {}

        def lookup(lookup_value):
            item = self.collection.find(key=lookup_value, method=self._read_given)
            if not item:
                raise AccessValueError(message='unable to find item key=%s, by=%s' %
                                               (_val, self._write_given))
            return item[self._read_item]

        for _key, _val in value.iteritems():
            if isinstance(_val, (list, dict)):
                retval[_key] = map(lookup, _val)
            else:
                retval[_key] = lookup(_val)

        return retval

    def xf_out(self, value):
        retval = {}

        def lookup(lookup_value):
            item = self.collection.find(key=lookup_value, method=self._write_given)
            if not item:
                raise AccessValueError(
                    message='unable to find item key=%s, by=%s' %
                            (_val, self._write_given))

            return item[self._write_item]

        for _key, _val in value.iteritems():
            if isinstance(_val, (list, dict)):
                retval[_key] = map(lookup, _val)
            else:
                retval[_key] = lookup(_val)

        return retval


class CollectionValueMultiTransformer(object):
    def __init__(self, session, xf_map):
        self.xfs = {
            id_name: CollectionValueTransformer(getattr(session, id_type))
            for id_name, id_type in xf_map.items()
        }

    def xf_in(self, values):
        return {
            id_name: self.xfs[id_name].xf_in({id_name: id_value})
            for id_name, id_value in values.items()
        }

    def xf_out(self, values):
        retval = {}
        for id_name, id_value in values.items():
            retval.update(self.xfs[id_name].xf_out({id_name: id_value}))
        return retval
