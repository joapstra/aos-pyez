# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

# import unittest
# from mock import patch
# import requests_mock
#


from utils.common import *

from apstra.aosom.collection_mapper import CollectionMapper, MultiCollectionMapper
from apstra.aosom.exc import *


class TestCollection(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestCollection, self).setUp()
        self.aos.login()

    def test_collection_exists(self):
        ip_pools = self.aos.IpPools
        assert ip_pools

    def test_collection_no_exists(self):
        try:
            _ = self.aos.IpPoolsBogus
        except SessionError:
            pass
        else:
            self.fail("SessionError not raised as expected")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_data_exist(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        # execute the cache collection
        _ = ip_pools.cache

        # clear cache, execute the collection of names
        ip_pools.cache.clear()
        _ = ip_pools.names

        # clear cache, execute the iterations
        ip_pools.cache.clear()
        _ = list(ip_pools)

        # execute the str()
        _ = str(ip_pools)

        # clear cache, get a specific named item
        a_name = ip_pools.names[0]
        ip_pools.cache.clear()
        _ = ip_pools[a_name]

    def test_collection_digest_fail(self):
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, status_code=400)
        try:
            ip_pools.cache.clear()
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_find(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        a_name = ip_pools.names[0]

        # clear cache, find by name
        ip_pools.cache.clear()
        ip_pools.find(label=a_name)

        # try to find a missing one
        this = ip_pools.find(label='this does not exist')
        self.assertEquals(this, None)

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_find_bad_args(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        _ = ip_pools.names[0]

        # clear cache, call find without any params
        ip_pools.cache.clear()
        try:
            ip_pools.find()
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError not raised as expected")

        # call find with both label and uid
        try:
            ip_pools.find(uid='this', label='that')
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError not raised as expected")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_test_operator_in(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        # clear cache, run a test
        ip_pools.cache.clear()
        results = 'this is a name' in ip_pools
        self.assertIsInstance(
            results, bool, msg="results are not a bool as expectect")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_test_operator_iadd(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        # make a copy, using a new name
        copy_of = ip_pools[ip_pools.names[0]]
        copy_of.value[ip_pools.LABEL] = 'NewOne'
        self.adapter.register_uri('POST', ip_pools.url, status_code=201)

        # clear cache, add item
        ip_pools.cache.clear()
        ip_pools += copy_of

    def test_collection_test_operator_iadd_fail_bad_item(self):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=dict(items=[]))

        # try to remove something that is not a CollectionItem
        not_an_item = dict(name='jeremy', state='NC')

        try:
            # now remove it
            ip_pools += not_an_item
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError not raised as expected")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_test_operator_isub(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        # get a known item.
        item = ip_pools[ip_pools.names[0]]

        # now remove it
        ip_pools -= item

    def test_collection_test_operator_isub_fail_bad_item(self):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=dict(items=[]))

        # try to remove something that is not a CollectionItem
        not_an_item = dict(name='jeremy', state='NC')

        try:
            # now remove it
            ip_pools -= not_an_item
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError not raised as expected")

    @mock_server_json_data_named('ip_pools', testcase='*')
    def test_collection_test_operator_isub_fail_item_noexist(self, json_data):
        # try to remove an IpPool Item from an AsnPool

        ip_pools = self.aos.IpPools
        asn_pools = self.aos.AsnPools

        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])
        self.adapter.register_uri('GET', asn_pools.url, json=dict(items=[]))

        asn_pools = self.aos.AsnPools

        ip_item = ip_pools[ip_pools.names[0]]
        try:
            asn_pools -= ip_item
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError not raised as expected")

    @mock_server_json_data_named(named='ip_pools', testcase='*')
    def test_collection_mapper(self, json_data):
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        xf = CollectionMapper(ip_pools)
        to_ids = xf.from_label(dict(items=ip_pools.names))
        to_labels = xf.from_uid(to_ids)

        # verify that the mapped items are there
        self.assertTrue(all([ip_pools.find(uid=_id) for _id in to_ids['items']]))
        self.assertTrue(all([ip_pools.find(label=_label) for _label in to_labels['items']]))

        # now add items to create value name->id mapping failures

        ip_pools.names.append('name_does_not_exist')
        try:
            to_ids = xf.from_label(dict(items=ip_pools.names))
        except AccessValueError:
            pass
        else:
            self.fail("AccessValueError not raised as expected")

        # now add items to create value id->name mapping failures

        to_ids['items'].append('id_does_not_exist')
        try:
            to_labels = xf.from_uid(to_ids)
        except AccessValueError:
            pass
        else:
            self.fail("AccessValueError not raised as expected")

    @mock_server_json_data_named(named='test_resources_in_use', testcase='TestMiscCollections')
    def test_collection_multi_mapper(self, json_data):
        ip_pools = self.aos.IpPools
        asn_pools = self.aos.AsnPools

        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])
        self.adapter.register_uri('GET', asn_pools.url, json=json_data[1])

        xfm = MultiCollectionMapper(
            self.aos, dict(ip_items='IpPools', asn_items='AsnPools'))

        to_ids = xfm.from_label(dict(
            ip_items=ip_pools.names,
            asn_items=asn_pools.names
        ))

        xfm.from_uid(to_ids)
