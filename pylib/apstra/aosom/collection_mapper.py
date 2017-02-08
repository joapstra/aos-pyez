# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from apstra.aosom.exc import AccessValueError

__all__ = [
    'CollectionMapper',
    'MultiCollectionMapper'
]


class CollectionMapper(object):
    """
    A CollectionMapper is used to map a collection item's unique-ID value (used by AOS)
    between the human usable value, e.g. the "display_name".  For example, let's presume
    you have an IpPools that contains the following:

        # >>> aos.IpPools
        # {
        #    "url": "resources/ip-pools",
        #    "by_id": "id",
        #    "item-names": [
        #       "Switches-IpAddrs",
        #       "Servers-IpAddrs"
        #    ],
        #    "by_label": "display_name"
        # }

    And then let's presume that you're given a list of UID values that represents these
    IpPools.  Because generally speaking the AOS API maintains relationships based on the UID
    values and not by the label values (which the User could change).  So here are the values:

        # >>> for each in aos.IpPools:
        # ...    print each.name, each.id
        # ...
        # Switches-IpAddrs 65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0
        # Servers-IpAddrs 0310d821-d075-4075-bdda-55cc6df57258

    So lets's say you're given a list of UID values:

        # data = dict(my_uids=[
        #     '65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0',
        #     '0310d821-d075-4075-bdda-55cc6df57258'])

    And you want the label values, then you would use the `from_uid` method:

        # >>> xf = CollectionMapper(aos.IpPools)
        # >>> xf.from_uid(data)
        # {'my_uids': [u'Switches-IpAddrs', u'Servers-IpAddrs']}

    And if you were given a list of names, and you needed the UIDs, then you would
    use the `from_label` method:

        # >>> human = {'my_uids': [u'Switches-IpAddrs', u'Servers-IpAddrs']}
        # >>> xf.from_label(human)
        # {'my_uids': [u'65dfbc77-1c77-4a99-98a6-e36c5aa7e4d0', u'0310d821-d075-4075-bdda-55cc6df57258']}
    """
    def __init__(self, collection,
                 read_given=None, read_item=None,
                 write_given=None, write_item=None):

        self.collection = collection
        self._read_given = read_given or collection.UNIQUE_ID
        self._read_item = read_item or collection.LABEL
        self._write_given = write_given or collection.LABEL
        self._write_item = write_item or collection.UNIQUE_ID

    def from_uid(self, items):
        """
        Transforms the native API stored value, i.e. unique-id, into something human "label value,
        i.e., 'display-name'.

        Args:
            items (dict): key is user defined, value is a string or collection of strings

        Returns:
            (dict): same key found in items, value is transformed values
        """

        def lookup(lookup_value):
            item = self.collection.find(uid=lookup_value)
            if not item:
                raise AccessValueError(
                    message='unable to find item key=%s, by=%s' %
                            (lookup_value, self._write_given))

            return item.value[self._read_item]

        return {
            _key: map(lookup, _val) if isinstance(_val, (list, dict)) else lookup(_val)
            for _key, _val in items.items()
        }

    def from_label(self, items):
        """
        Transforms the human "label value, i.e., 'display-name', to the native API stored value,
        i.e. unique-id, into something

        Args:
            items (dict): key is user defined, value is a string or collection of strings

        Returns:
            (dict): same key found in items, value is transformed values
        """
        def lookup(lookup_value):
            item = self.collection.find(label=lookup_value)
            if not item:
                raise AccessValueError(
                    message='unable to find item key=%s, by=%s' %
                            (lookup_value, self._write_given))

            return item.value[self._write_item]

        return {
            _key: map(lookup, _val) if isinstance(_val, (list, dict)) else lookup(_val)
            for _key, _val in items.items()
        }


class MultiCollectionMapper(object):
    def __init__(self, session, xf_map):
        self.xfs = {
            id_name: CollectionMapper(getattr(session, id_type))
            for id_name, id_type in xf_map.items()
        }

    def from_uid(self, values):
        retval = {}
        for id_name, id_value in values.items():
            retval.update(self.xfs[id_name].from_uid({id_name: id_value}))
        return retval

    def from_label(self, values):
        retval = {}
        for id_name, id_value in values.items():
            retval.update(self.xfs[id_name].from_label({id_name: id_value}))
        return retval
