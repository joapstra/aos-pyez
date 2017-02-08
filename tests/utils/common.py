# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import json
import inspect
from os import path
from glob import glob

import unittest
from mock import patch
import requests_mock

from apstra.aosom.session import Session
from config import Config

__all__ = [
    'load_mock_server_json_data',
    'mock_server_json_data',
    'mock_server_json_data_named',
    'AosPyEzCommonTestCase'
]

mock_server_json_dir = path.join(path.dirname(
    path.realpath(__file__)), "..",
    'mock_server_data')


def load_mock_server_json_data(cls_name, named):

    filepath = path.join(mock_server_json_dir, "{}.{}*.json".format(
        cls_name, named))

    json_data = [json.load(open(f_name)) for f_name in glob(filepath)]
    if not json_data:
        raise RuntimeError("No JSON files for '{}'".format(filepath))

    return json_data


def mock_server_json_data(method):
    cls_name = inspect.stack()[1][3]

    def decorate_method(self, *vargs, **kwargs):
        return method(self,
                      load_mock_server_json_data(cls_name, method.__name__),
                      *vargs, **kwargs)

    return decorate_method


def mock_server_json_data_named(named, testcase=None):

    def param_decorate(method):
        cls_name = testcase or inspect.stack()[1][3]

        def decorate_method(self, *vargs, **kwargs):
            return method(self,
                          load_mock_server_json_data(cls_name, named),
                          *vargs, **kwargs)

        return decorate_method

    return param_decorate


# noinspection PyUnresolvedReferences
class AosPyEzCommonTestCase(unittest.TestCase):

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
