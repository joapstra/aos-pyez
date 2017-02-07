# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import os

from apstra.aosom.dynmodldr import DynamicModuleOwner

from apstra.aosom.exc import (
    LoginServerUnreachableError,
    NoLoginError, LoginNoServerError)

from .session_api import Api

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

    Api = Api

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

    @property
    def token(self):
        """
        Returns: (str) - authentication token from login/resume

        Raises:
            - NoLoginError: if no token is present
        """
        try:
            return self.api.token
        except:
            raise NoLoginError()

    @property
    def session(self):
        """
        Returns the 'session' information that can be later used to to resume
        a previous token-session

        Returns: (dict) containing session information required 'resume'
        """
        return {
            'server': self.server,
            'port': self.port,
            'token': self.token
        }

    @session.setter
    def session(self, prev_session):
        """
        Attempts to resume an existing session with the AOS-server using the
        provided session data.  If there is an error, an exception is raised.

        Args:
            prev_session (dict): previous session data

        Raises:
            See Session.Api.resume for list of exceptions
        """
        try:
            self.server = prev_session['server']
            self.port = prev_session['port']
            token = prev_session['token']
        except KeyError as exc:
            raise RuntimeError("Invalid session data, missing '{}'".format(exc.message))

        self.api.set_url(self.server, self.port)
        self.api.token = token
        self.api.resume()

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
            - LoginNoServerError:
                when the instance does not have :attr:`server` configured

            - LoginServerUnreachableError:
                when the API is not able to connect to the AOS-server via the API.
                This could be due to any number of networking related issues.
                For example, the :attr:`port` is blocked by a firewall, or the :attr:`server`
                value is IP unreachable.
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
