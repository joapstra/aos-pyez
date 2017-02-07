# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from apstra.aosom.exc import *
from aos_pyez_unittest_common import *


class TestMiscCollections(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestMiscCollections, self).setUp()
        self.aos.login()

    def test_dynload_catalog(self):
        for widget in self.aos.ModuleCatalog:
            getattr(self.aos, widget)

    @mock_server_json_data
    def test_resources_in_use(self, json_data):
        ip_pools = self.aos.IpPools
        asn_pools = self.aos.AsnPools

        self.adapter.register_uri('GET', ip_pools.url, json=json_data[0])
        self.adapter.register_uri('GET', asn_pools.url, json=json_data[1])

        item = ip_pools[ip_pools.names[0]]
        self.assertTrue(item.in_use)

        item = asn_pools[asn_pools.names[0]]
        self.assertTrue(item.in_use)


