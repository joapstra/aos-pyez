# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from utils.common import *
from apstra.aosom.exc import *


class TestBlueprintModules(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestBlueprintModules, self).setUp()
        self.aos.login()

        json_data = load_mock_server_json_data(
            cls_name=self.__class__.__name__,
            named='contents')

        self.blueprints = self.aos.Blueprints

        self.adapter.register_uri('GET', self.blueprints.url, json=json_data[0])
        self.bp_item = self.blueprints[self.blueprints.names[0]]

        self.adapter.register_uri('GET', self.bp_item.url, json=json_data[1])
        self.adapter.register_uri('GET', self.bp_item.params.url, json=json_data[2])

        self.bp_digest_data = json_data[0]
        self.bp_item_data = json_data[1]
        self.bp_item_params_data = json_data[2]

    def test_blueprint_dynloader(self):
        for mod in self.bp_item.ModuleCatalog:
            getattr(self.bp_item, mod)

    def test_blueprint_slots(self):
        _ = [p for p in self.bp_item.params]
        _ = [i.info for i in self.bp_item.params]
        _ = str(self.bp_item.params)

        p_name = self.bp_item.params.names[0]
        self.assertTrue(p_name in self.bp_item.params)

        # clear cache, force index lookup
        self.bp_item.params.cache.clear()
        p_item = self.bp_item.params[p_name]
        self.assertIsNotNone(p_item)

        # clear cache, re-digest
        self.bp_item.params.cache.clear()
        _ = self.bp_item.params.cache

        # clear cache, re-digest, mock error
        self.bp_item.params.cache.clear()
        self.adapter.register_uri('GET', self.bp_item.params.url, status_code=400)

        try:
            _ = self.bp_item.params.cache
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")
        finally:
            # restore
            self.adapter.register_uri('GET', self.bp_item.params.url, json=self.bp_item_params_data)

    @mock_server_json_data
    def test_blueprint_slot_data(self, json_data):
        # register each of the slot GETs to respective data

        for p in self.bp_item.params:
            self.adapter.register_uri('GET', p.url, json=json_data[0][p.name])

        if __name__ == '__main__':
            for p in self.bp_item.params:
                _ = str(p)

        # clear an item
        p_names = self.bp_item.params.names
        p_0 = self.bp_item.params[p_names[0]]

        # clear an item, mock the failure
        self.adapter.register_uri('PUT', p_0.url, status_code=400)
        try:
            p_0.clear()
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

        # clear an item, OK
        self.adapter.register_uri('PUT', p_0.url, status_code=200)
        p_0.clear()

        # write an item value property, OK
        p_0.value = dict(name='jeremy', state='NC')

        # clear an item value property, OK
        del p_0.value

        # get an item value property
        _ = p_0.value
        _ = str(p_0)

        # read, with mock failure
        self.adapter.register_uri('GET', p_0.url, status_code=400)
        try:
            _ = p_0.value
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

        # to a an update / PATCH on an item, ok

        patch_data = dict(name='jeremy', state='NC')

        def do_patch(rqst, context):
            context.status_code = 200
            self.assertEquals(rqst.json(), patch_data)

        self.adapter.register_uri('PATCH', p_0.url, json=do_patch)

        def read_back(_, context):
            context.status_code = 200
            return patch_data

        self.adapter.register_uri('GET', p_0.url, json=read_back)

        p_0.update(patch_data)
        self.assertEquals(p_0.value, patch_data)

        # patch, mock an error
        self.adapter.register_uri('PATCH', p_0.url, status_code=400)
        try:
            p_0.update(patch_data)
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")
