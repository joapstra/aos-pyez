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
from apstra.aosom.exc import (
    LoginError, LoginServerUnreachableError, LoginAuthError,
    NoLoginError, LoginNoServerError)


__all__ = ['Session']


class Session(DynamicModuleOwner):
    """
    The Session class is used to create a client connection with the AOS-server.  The general
    process to create a connection is as follows::

        from apstra.aosom.session import Session

        aos = Session('aos-session')                  # hostname or ip-addr of AOS-server
        aos.login()                                   # username/password uses defaults

        print aos.api.version
        # >>> {u'major': u'1', u'version': u'1.0',
                'semantic': Version('1.0', partial=True), u'minor': u'0'}

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
            self.server = None
            self.port = None
            self.url = None
            self.version = None
            self.semantic_ver = None
            self.headers = {}

        def set_url(self, server, port):
            """
            Method used to setup the AOS-server URL given the `server` and `port`
            arguments.

            Args:
                server (str): server-name/ip-address (does not include the http:// prefix)
                port (int): the AOS server port
            """
            self.server = server
            self.port = port
            self.url = "http://{server}:{port}/api".format(server=server, port=port)

        def resume(self, url, headers):
            """
            Method used to resume the use of the provided `url` and `header` values.
            The `header` values are expected to include the previous values as provided
            from the use of the :meth:`login`.

            Args:
                url (str): complete URL to the AOS-server API
                headers (dict): contains the previous auth token

            Raises:
                - LoginError: the provided `url` does not contain "/api"
                - LoginServerUnreachableError: when the probe of AOS server fails
                - LoginError: unable to get the version information
                - LoginAuthError: the `headers` do not contain valid token
            """
            if 'api' not in url:
                raise LoginError(
                    message='missing "/api" in URL: [{}]'.format(url))

            # extract the server and port information because we
            # need this for the probe method

            self.server, self.port = url.split('/')[2].split(':')

            if not self.probe():
                raise LoginServerUnreachableError(
                    message="Trying URL: [{}]".format(url))

            self.url = copy(url)
            self.headers = copy(headers)

            try:
                self.get_ver()
            except:
                raise LoginError(
                    message='unable get AOS-server version via API: [{}]'.format(url))

            if not self.verify_token():
                raise LoginAuthError()

        def login(self, user, passwd):
            """
            Method used to "login" to the AOS-server and acquire the auth token for future
            API calls.

            Args:
                user (str): user account name
                passwd (str): user password

            Raises:
                - LoginAuthError: if the provided `user` and `passwd` values do not
                    authenticate with the AOS-server
            """
            rsp = requests.post(
                "%s/user/login" % self.url,
                json=dict(username=user, password=passwd))

            if not rsp.ok:
                raise LoginAuthError()

            self.headers['AUTHTOKEN'] = rsp.json()['token']
            self.get_ver()

        def get_ver(self):
            """
            Used to retrieve the AOS API version information.

            Raises:
                - ValueError: the retrieve version string is not semantically valid
            """
            got = requests.get("%s/versions/api" % self.url)
            self.version = copy(got.json())

            try:
                self.version['semantic'] = semantic_version.Version(self.version['version'])
            except ValueError:
                self.version['semantic'] = semantic_version.Version(self.version['version'], partial=True)

            return self.version

        def verify_token(self):
            """
            This method is used to verify that the existing AUTHTOKEN is still valid.

            Returns:
                - True if it is
                - False if it is not
            """
            got = requests.get('%s/user' % self.url, headers=self.headers)
            return got.ok

        def probe(self, timeout=5, intvtimeout=1):
            """
            Used to probe the AOS-server to ensure that it is IP reachable.  This
            is done prior to attempting to use the API for REST calls; simply to
            avoid a long timeout

            Args:
                timeout (int): seconds before declaring unreachable
                intvtimeout (int): seconds between each attempt

            Returns:
                - True: AOS server is reachable
                - False: if not
            """
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
        """
        Property to return the current AOS-server API URL.  If this value is
        not set, then an exception is raised.  The raise here is important
        because other code depends on this behavior.

        Returns: (str) API URL

        Raises:
            - NoLoginError: URL does not exist
        """
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

        self.api.set_url(server=self.server, port=self.port)

        if not self.api.probe():
            raise LoginServerUnreachableError()

        self.api.login(self.user, self.passwd)

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PRIVATE METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def _set_login(self, **kwargs):
        """
        Used to configure login parameters.

        Args:
            **kwargs: see __init__ for details
        """
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
