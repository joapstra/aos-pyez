# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import unittest
from mock import patch
import requests_mock

from apstra.aosom.session import Session
from apstra.aosom.exc import *

from config_unittests import Config


# noinspection PyUnresolvedReferences
class TestAosomSession(unittest.TestCase):
    """
    Test cases to verify the functionality of the Session object, mainly focused
    around the various login pass/failure cases.
    """

    def setUp(self):

        self.adapter = requests_mock.Adapter()
        self.aos = Session(Config.test_server)
        self.aos.api.requests.mount('http://%s' % Config.test_server, self.adapter)

        self.adapter.register_uri(
            'GET', '/api/versions/api',
            json=dict(version=Config.test_server_version))

        self.adapter.register_uri(
            'POST', '/api/user/login', json=dict(token=Config.test_auth_token))

        # generally enable the probe step to pass
        patch.object(self.aos.api, 'probe', return_value=True).start()

    def test_login_pass(self):
        self.aos.login()
        self.assertEquals(self.aos.token, "GoodToken")
        self.assertEquals(self.aos.api.version['version'], Config.test_server_version)

    def test_login_no_server(self):
        had_server = self.aos.server
        self.aos.server = None
        try:
            self.aos.login()
        except LoginNoServerError:
            pass
        else:
            self.assertTrue(False, msg='LoginNoServerError not raised as expected')
        finally:
            self.aos.server = had_server

    def test_login_unreachable_server(self):
        try:
            # noinspection PyUnresolvedReferences
            with patch.object(self.aos.api, 'probe', return_value=False):
                self.aos.login()
        except LoginServerUnreachableError:
            pass
        else:
            self.assertTrue(
                False, msg='LoginServerUnreachableError not raised as expected')

    def test_login_bad_credentials(self):
        self.adapter.register_uri('POST', '/api/user/login', status_code=400)

        try:
            self.aos.login()
        except LoginAuthError:
            pass
        else:
            self.assertTrue(
                False, msg='LoginAuthError not raised as expected')

    # ##### -------------------------------------------------------------------
    # ##### resume session test cases
    # ##### -------------------------------------------------------------------

    @staticmethod
    def validate_token(request, context):
        context.status_code = [400, 200][int(request.headers['AUTHTOKEN'] == Config.test_auth_token)]
        return {}

    def test_login_resume_pass(self):
        self.adapter.register_uri('GET', '/api/user', json=self.validate_token)
        self.aos.resume(token=Config.test_auth_token)

    def test_login_resume_bad_token(self):
        self.adapter.register_uri('GET', '/api/user', json=self.validate_token)

        try:
            self.aos.resume(token='i am a bad token')
        except LoginAuthError:
            pass
        else:
            self.assertTrue(False, msg='LoginAuthError not raised as expected')

    def test_login_resume_bad_url(self):
        self.adapter.register_uri('GET', '/api/user', json=self.validate_token)

        try:
            self.aos.resume(server=Config.test_server, token=Config.test_auth_token)
            # this way is not, but using it for test point
            self.aos.api.resume(url=Config.test_auth_token,
                                headers=dict(AUTHTOKEN=Config.test_auth_token))
        except LoginError:
            pass
        else:
            self.assertTrue(False, msg='LoginError not raised as expected')

    def test_login_resume_unreachable_server(self):
        self.adapter.register_uri('GET', '/api/user', json=self.validate_token)

        try:
            with patch.object(self.aos.api, 'probe', return_value=False):
                self.aos.resume(token=Config.test_auth_token)
        except LoginServerUnreachableError:
            pass
        else:
            self.assertTrue(
                False, msg='LoginServerUnreachableError not raised as expected')

    # ##### -------------------------------------------------------------------
    # ##### test probing against real target
    # ##### -------------------------------------------------------------------

    def test_probe_real_target_ok(self):
        test_target = Session.Api()
        test_target.set_url(server='www.google.com', port=80)
        self.assertTrue(test_target.probe())

    def test_probe_real_target_fail(self):
        test_target = Session.Api()
        test_target.set_url(server='www.google.com', port=81)
        self.assertFalse(test_target.probe())

    # ##### -------------------------------------------------------------------
    # ##### test misc properties
    # ##### -------------------------------------------------------------------

    def test_property_token_missing(self):
        try:
            _ = self.aos.token
        except NoLoginError:
            pass
        else:
            self.assertTrue(
                False, msg='NoLoginError not raised as expected')

    def test_property_token_ok(self):
        self.aos.login()
        self.assertEquals(self.aos.api.headers['AUTHTOKEN'], Config.test_auth_token)

    def test_property_url_missing(self):
        try:
            _ = self.aos.url
        except NoLoginError:
            pass
        else:
            self.assertTrue(
                False, msg='NoLoginError not raised as expected')

    def test_property_url_ok(self):
        self.aos.login()
        _ = self.aos.url
