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
import semantic_version

from apstra.aosom.exc import LoginAuthError, LoginNoServerError, LoginServerUnreachableError
from apstra.aosom.exc import SessionError
from apstra.aosom.amods import AosModuleCatalog

__all__ = ['Session']


class Session(object):
    """
    The Session class is used to create a client connection with the AOS-server.  The general
    process to create a connection is as follows::

        from apstra.aosom.session import Session

        aos = Session('aos-session')                  # hostname or ip-addr of AOS-server
        aos.login()                                   # username/password uses defaults

    This module will use your environment variables to provde the default login values,
    if they are set.  Refer to :data:`~Session.ENV` for specific values.

    This module will use value defaults as defined in :data:`~Session.DEFAULTS`.

    Once you have an active session with the AOS-server you the aos-pyez modules as
    defined in the :data:`~Session.ModuleCatalog`.
    """
    ModuleCatalog = AosModuleCatalog.keys()

    ENV = {
        'SERVER': 'AOS_SERVER',
        'PORT': 'AOS_SERVER_PORT',
        'TOKEN': 'AOS_SESSION_TOKEN',
        'USER': 'AOS_USER',
        'PASSWD': 'AOS_PASSWD'
    }

    DEFAULTS = {
        'USER': 'admin',
        'PASSWD': 'admin',
        'PORT': 8888
    }

    class Api(object):
        def __init__(self):
            self.url = None
            self.version = None
            self.semantic_ver = None
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
            self.version = copy(got.json())
            self.version['semantic'] = semantic_version.Version(self.version['version'], partial=True)
            return self.version

        def accept_token(self, token):
            self.headers['AUTHTOKEN'] = token

    def __init__(self, server=None, **kwargs):
        self.user, self.passwd = (None, None)
        self.server, self.port = (server, None)
        self.api = Session.Api()
        self._set_login(server=server, **kwargs)

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PUBLIC METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def login(self):
        """
        Login to the AOS-server, obtaining a session token for use with later
        calls to the API.

        Raises:
            LoginNoServerError:
                when the instance does not have :attr:`server` configured

            LoginServerUnreachableError:
                when the API is not able to connect to the AOS-server via the API.
                This could be due to any number of networking related issues.
                For example, the :attr:`port` is blocked by a firewall, or the :attr:`server`
                value is IP unreachable.

        Returns:
            None
        """
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
        self.server = kwargs.get('server') or os.getenv(Session.ENV['SERVER'])

        self.port = kwargs.get('port') or \
            os.getenv(Session.ENV['PORT']) or \
                    Session.DEFAULTS['PORT']

        self.user = kwargs.get('user') or \
            os.getenv(Session.ENV['USER']) or \
                    Session.DEFAULTS['USER']

        self.passwd = kwargs.get('passwd') or \
            os.getenv(Session.ENV['PASSWD']) or \
                      Session.DEFAULTS['PASSWD']

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
