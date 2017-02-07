# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

# import unittest
# from mock import patch
# import requests_mock
#

import json
import os
from copy import copy

from apstra.aosom.exc import *
from aos_pyez_unittest_common import *


class TestCollectionItems(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestCollectionItems, self).setUp()
        self.aos.login()

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_exists(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        a_name = ip_pools.names[0]
        by_name = ip_pools[a_name]
        _ = by_name.url

        self.assertEquals(by_name.name, a_name)
        self.assertEquals(by_name.value[ip_pools.UNIQUE_ID], by_name.id)
        self.assertTrue(by_name.exists)
        _ = str(by_name)

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_noexists(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        by_name = ip_pools['i do not exist']
        try:
            _ = by_name.url
        except NoExistsError:
            pass
        else:
            self.fail("NoExistsError not raised as expected")

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_jsonfile(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]
        item.jsonfile_save()

        filename = "{}.json".format(item.name)
        self.assertEquals(item.value, json.load(open(filename)))

        new_item = ip_pools['new_item']
        new_item.jsonfile_load(filepath=filename)

        os.remove(filename)

    @mock_server_json_data
    def test_collection_item_read(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]
        self.adapter.register_uri('GET', item.url, json=json_data[1])

        # this should be A-OK
        self.assertEquals(item.read(), json_data[1])

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_read_fail(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]

        # hack the item ID value to cause a failure in the GET
        bad_id = "i_am_bad"
        self.adapter.register_uri('GET', ip_pools.url + "/%s" % bad_id,
                                  status_code=400)

        item.value[ip_pools.UNIQUE_ID] = 'i_am_bad'
        try:
            item.read()
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    @mock_server_json_data
    def test_collection_item_create(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        new_item = ip_pools['i_am_new']

        # try to create; this should fail because the read data actually already exists
        # and the create method does not look at the value data to reset the label value.

        try:
            new_item.create(value=json_data[1])
        except DuplicateError:
            pass
        else:
            self.fail("DuplicateError not raised as expected")

        # now change the label value and re-attempt the create
        new_value = json_data[1]
        new_value[ip_pools.LABEL] = new_item.name

        self.adapter.register_uri('POST', ip_pools.url, status_code=201, json={'id': 'fake_id'})
        new_item.create(value=new_value)
        self.assertEquals(new_item.id, 'fake_id')

        # now try to create it again without replace, expect a duplicate error

        try:
            new_item.create()
        except DuplicateError:
            pass
        else:
            self.fail("DuplicateError not raised as expected")

        # now try to create it again with replace=True to overwrite it.
        # this process will first DELETE, so we need to mock that

        self.adapter.register_uri('DELETE', new_item.url, status_code=200)
        new_item.create(replace=True)

        # delete it, and now try to create it, simulate a POST failure
        del new_item.value
        self.adapter.register_uri('POST', ip_pools.url, status_code=400)
        try:
            new_item.create()
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_delete(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]

        self.adapter.register_uri('DELETE', item.url, status_code=200)
        del item.value

    @mock_server_json_data_named('ip_pools')
    def test_collection_item_delete_fail(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]

        self.adapter.register_uri('DELETE', item.url, status_code=400)
        try:
            del item.value
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    @mock_server_json_data_named('test_collection_item_create')
    def test_collection_item_write(self, json_data):
        # use the IpPools as an example collection
        ip_pools = self.aos.IpPools
        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])

        item = ip_pools[ip_pools.names[0]]
        item.value['subnets'].append(dict(network="1.1.1.0/24"))

        copy_write = copy(item.value)

        # mock the PUT, and GET
        self.adapter.register_uri('PUT', item.url, status_code=200)
        self.adapter.register_uri('GET', item.url, json=item.value)

        # verify we got back what we mock-wrote
        item.write()
        self.assertEquals(item.value, copy_write)

        # mock a bad PUT
        self.adapter.register_uri('PUT', item.url, status_code=400)
        try:
            item.write()
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

        # now attempt a write on something that doesn't exist,
        # need to mock a GET and POST

        new_item = ip_pools['I_am_new']

        self.adapter.register_uri('GET', item.url, json=new_item.value)
        self.adapter.register_uri('POST', ip_pools.url, json=dict(id='fake_id'))

        new_item.write(value={ip_pools.LABEL: new_item.name})
        self.assertEquals(new_item.id, 'fake_id')

