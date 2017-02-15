# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from utils.common import *

from apstra.aosom.exc import *


class TestBlueprintCollection(AosPyEzCommonTestCase):

    def setUp(self):
        super(TestBlueprintCollection, self).setUp()
        self.aos.login()

        json_data = load_mock_server_json_data(
            cls_name=self.__class__.__name__,
            named='contents')

        self.blueprints = self.aos.Blueprints

        self.adapter.register_uri('GET', self.blueprints.url, json=json_data[0])
        self.bp_item = self.blueprints[self.blueprints.names[0]]

        self.adapter.register_uri('GET', self.bp_item.url, json=json_data[1])

        self.bp_digest_data = json_data[0]
        self.bp_item_data = json_data[1]

    def test_blueprint_contents(self):
        blueprints = self.aos.Blueprints
        item = blueprints[blueprints.names[0]]

        # check the 'contents' property
        self.assertEquals(item.contents, self.bp_item_data)

        # check the build_errors property, should be None
        self.assertIsNone(item.build_errors)

        # mock the failure of the getting the contents
        self.adapter.register_uri('GET', item.url, status_code=400)
        try:
            self.assertEquals(item.contents, self.bp_item_data)
        except SessionRqstError:
            pass
        else:
            self.fail("SessionRqstError not raised as expected")

    def test_blueprint_delete_contents(self):
        blueprints = self.aos.Blueprints

        item = blueprints[blueprints.names[0]]
        self.adapter.register_uri('DELETE', item.url, status_code=200)

        del item.contents

    def test_blueprint_await_build_ready(self):
        blueprints = self.aos.Blueprints
        item = blueprints[blueprints.names[0]]

        self.assertTrue(item.await_build_ready())

        # fake an error, await ready will return False

        self.bp_item_data['errors'] = ['i_am_an_error']
        try:
            assert item.await_build_ready()
        except AssertionError:
            pass
        else:
            self.fail("AssertionError not raised as expected")
        finally:
            # restore
            del self.bp_item_data['errors']

    def test_blueprint_create(self):
        blueprints = self.aos.Blueprints

        new_bp = blueprints['i_am_new']

        def mock_new_blueprint(_, context):
            context.status_code = 200
            return dict(id='fake_id')

        self.adapter.register_uri('POST', blueprints.url, json=mock_new_blueprint)

        result = new_bp.create(
            design_template_id='fake_template_id',
            reference_arch='fake_reference_arch')

        self.assertTrue(result)

        # now setup a failure case

        def mock_no_new_blueprint(_, context):
            context.status_code = 200
            return dict(id=None)

        self.adapter.register_uri('POST', blueprints.url, json=mock_no_new_blueprint)

        new_bp = blueprints['i_am_another_new']
        result = new_bp.create(
            design_template_id='fake_template_id',
            reference_arch='fake_reference_arch')

        self.assertFalse(result)

        # try again, but don't wait for response

        new_bp = blueprints['yes_another_new']
        self.adapter.register_uri('POST', blueprints.url, json=mock_new_blueprint)
        result = new_bp.create(
            blocking=False,
            design_template_id='fake_template_id',
            reference_arch='fake_reference_arch')

        self.assertTrue(result)
