# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula



from apstra.aosom.exc import *
from aos_pyez_unittest_common import *


class TestDevices(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestDevices, self).setUp()
        self.aos.login()

        self.devs = self.aos.Devices
        json_data = load_mock_server_json_data(cls_name='TestDevices', named='devices')
        self.devices = json_data[0]
        self.approved = json_data[1]

        self.adapter.register_uri('GET', self.devs.url, json=self.devices)
        self.adapter.register_uri('GET', self.devs.approved.url, json=self.approved)

    def test_devices_exist(self):
        ids = self.devs.approved.ids
        self.assertEquals(ids, [d['id'] for d in self.approved['devices']])

    def test_devices_get_approved_fail(self):
        self.adapter.register_uri('GET', self.devs.approved.url, status_code=400)
        try:
            _ = self.devs.approved.ids
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")
        finally:
            # restore
            self.adapter.register_uri('GET', self.devs.approved.url, json=self.approved)

    def test_devices_update_approved(self):
        self.adapter.register_uri('PUT', self.devs.approved.url, status_code=200)
        self.devs.approved.update(device_keys=['this', 'that'])

        # test putting in values that already exist
        has_devids = self.devs.approved.ids
        self.devs.approved.update(has_devids)

        # mock update failure
        self.adapter.register_uri('PUT', self.devs.approved.url, status_code=400)
        try:
            self.devs.approved.update(device_keys=['this', 'that'])
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    def test_device_information(self):
        self.assertTrue(all([d.is_approved for d in self.devs]))

    def test_device_user_config(self):
        dev = self.devs[self.devs.names[0]]

        def fetch_device(_, context):
            context.status_code = 200
            return self.devs.find(uid=dev.id).value

        self.adapter.register_uri('GET', dev.url, json=fetch_device)

        _ = dev.user_config
        _ = dev.state

        # set user_config
        # patch the PUT

        value = {
            "aos_hcl_model": "Bogus-HCL",
            "admin_state": "normal",
            "location": "rack-12"
        }

        def verify(request, context):
            self.assertEquals(request.json(), dict(user_config=value))
            context.status_code = 200

        self.adapter.register_uri('PUT', dev.url, json=verify)
        dev.user_config = value

        # go again with fail mock
        self.adapter.register_uri('PUT', dev.url, status_code=400)
        try:
            dev.user_config = value
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    def test_device_approve(self):
        dev = self.devs[self.devs.names[0]]

        # this one is already approved, so the return should be False
        self.assertFalse(dev.approve(location='here'))

        # now hack the state to be OOS-QUARANTINED, and re-attempt
        dev.value['status']['state'] = 'OOS-QUARANTINED'

        location = 'here'
        def do_approve(request, context):
            context.status_code = 200
            body = request.json()
            self.assertEquals(location, body['user_config']['location'])
            return {}

        self.adapter.register_uri('PUT', dev.url, json=do_approve)
        dev.approve(location=location)



