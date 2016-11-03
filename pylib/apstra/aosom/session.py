# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import os
import datetime
import socket
import time
import importlib

from copy import copy

import requests

from apstra.aosom.exc import LoginAuthError, LoginNoServerError, LoginServerUnreachableError
from apstra.aosom.exc import SessionError
from apstra.aosom.amods import AosModuleCatalog

__all__ = ['Session']


class Session(object):
    ModuleCatalog = AosModuleCatalog.keys()

    _ENV = {
        'SERVER': 'AOS_SERVER',
        'PORT': 'AOS_SERVER_PORT',
        'TOKEN': 'AOS_SESSION_TOKEN',
        'USER': 'AOS_USER',
        'PASSWD': 'AOS_PASSWD'
    }

    _DEFAULTS = {
        'USER': 'admin',
        'PASSWD': 'admin',
        'PORT': 8888
    }

    class Api(object):
        def __init__(self):
            self.url = None
            self.ver = None
            self.headers = {}

        def set_url(self, server, port):
            self.url = "http://{server}:{port}/api".format(server=server, port=port)

        def resume(self, url, headers):
            self.url = copy(url)
            self.headers = copy(headers)
            self.get_ver()

        def login(self, user, passwd):
            rsp = requests.post(
                "%s/user/login" % self.url,
                json=dict(username=user, password=passwd))

            if not rsp.ok:
                raise LoginAuthError()

            self.accept_token(rsp.json()['token'])
            self.get_ver()

        def get_ver(self):
            got = requests.get("%s/versions/api" % self.url)
            self.ver = got.json()
            return self.ver

        def accept_token(self, token):
            self.headers['AUTHTOKEN'] = token

    def __init__(self, **kwargs):
        self.user, self.passwd = (None, None)
        self.server, self.port = (None, None)
        self.api = Session.Api()
        self._set_login(**kwargs)

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PUBLIC METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def login(self):
        if not self.server:
            raise LoginNoServerError()

        if not self._probe():
            raise LoginServerUnreachableError()

        self.api.set_url(server=self.server, port=self.port)
        self.api.login(self.user, self.passwd)

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PRIVATE METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def _set_login(self, **kwargs):
        self.server = kwargs.get('server') or os.getenv(Session._ENV['SERVER'])

        self.port = kwargs.get('port') or \
            os.getenv(Session._ENV['PORT']) or \
            Session._DEFAULTS['PORT']

        self.user = kwargs.get('user') or \
            os.getenv(Session._ENV['USER']) or \
            Session._DEFAULTS['USER']

        self.passwd = kwargs.get('passwd') or \
            os.getenv(Session._ENV['PASSWD']) or \
            Session._DEFAULTS['PASSWD']

    def _probe(self, timeout=5, intvtimeout=1):
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(intvtimeout)
            try:
                s.connect((self.server, int(self.port)))
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                return True
            except socket.error:
                time.sleep(1)
                pass
        else:
            # elapsed = datetime.datetime.now() - start
            return False

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         DYNAMIC MODULE LOADER
    # ###
    # ### ---------------------------------------------------------------------

    def __getattr__(self, amod_name):
        if amod_name not in AosModuleCatalog:
            raise SessionError(message='request for unknown module: %s' % amod_name)

        amod_file = AosModuleCatalog[amod_name]
        got = importlib.import_module(".amods.%s" % amod_file, package=__package__)
        cls = getattr(got, got.__all__[0])
        setattr(self, amod_name, cls(api=self.api))
        return getattr(self, amod_name)
