# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import os
import datetime
import socket
import time


from copy import copy

import requests
import semantic_version

from apstra.aosom.dynmodldr import DynamicModuleOwner
from apstra.aosom.exc import NoLoginError, LoginAuthError, LoginNoServerError
from apstra.aosom.exc import LoginServerUnreachableError

__all__ = ['Session']


class Session(DynamicModuleOwner):
    """
    The Session class is used to create a client connection with the AOS-server.  The general
    process to create a connection is as follows::

        from apstra.aosom.session import Session

        aos = Session('aos-session')                  # hostname or ip-addr of AOS-server
        aos.login()                                   # username/password uses defaults

        print aos.api.version
        >>> {u'major': u'1', u'version': u'1.0', 'semantic': Version('1.0', partial=True), u'minor': u'0'}

    This module will use your environment variables to provide the default login values,
    if they are set.  Refer to :data:`~Session.ENV` for specific values.

    This module will use value defaults as defined in :data:`~Session.DEFAULTS`.

    Once you have an active session with the AOS-server you use the modules defined in the
    :data:`~Session.ModuleCatalog`.

    The following are the available public attributes of a Session instance:
        * `api` - an instance of the :class:`Session.Api` that provides HTTP access capabilities.
        * `server` - the provided AOS-server hostname/ip-addr value.
        * `user` - the provided AOS login user-name

    The following are the available user-shell environment variables that are used by the Session instance:
        * :data:`AOS_SERVER` - the AOS-server hostname/ip-addr
        * :data:`AOS_SERVER_PORT` - the AOS-server API port, defaults to :data:`~DEFAULTS[\"PORT\"]`.
        * :data:`AOS_USER` - the login user-name, defaults to :data:`~DEFAULTS[\"USER\"]`.
        * :data:`AOS_PASSWD` - the login user-password, defaults to :data:`~DEFAULTS[\"PASSWD\"]`.
        * :data:`AOS_SESSION_TOKEN` - a pre-existing API session-token to avoid user login/authentication.
    """
    DYNMODULEDIR = '.session_modules'

    #    ModuleCatalog = AosModuleCatalog.keys()

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
        """
        Create a Session instance that will connect to an AOS-server, `server`.  Additional
        keyword arguments can be provided that override the default values, as defined
        in :data:`~Session.DEFAULTS`, or the values that are taken from the callers shell
        environment, as defined in :data:`~Session.ENV`.  Once a Session instance has been
        created, the caller can complete the login process by invoking :meth:`login`.

        Args:
            server (str): the hostname or ip-addr of the AOS-server.

        Keyword Args:
            user (str): the login user-name
            passwd (str): the login password
            port (int): the AOS-server API port
        """
        self.user, self.passwd = (None, None)
        self.server, self.port = (server, None)
        self.api = Session.Api()
        self._set_login(server=server, **kwargs)

    @property
    def url(self):
        if not self.api.url:
            raise NoLoginError(
                "not logged into server '{}:{}'".format(self.server, self.port))

        return self.api.url

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
