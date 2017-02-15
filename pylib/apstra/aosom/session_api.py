# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import datetime
import socket
import time


from copy import copy

import requests
import semantic_version

from apstra.aosom.exc import LoginServerUnreachableError, LoginAuthError


class Api(object):

    def __init__(self):
        self.server = None
        self.port = None
        self.url = None
        self.version = None
        self.semantic_ver = None
        self.requests = requests.Session()

    @property
    def token(self):
        return self.requests.headers['AUTHTOKEN']

    @token.setter
    def token(self, value):
        self.requests.headers['AUTHTOKEN'] = value

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

    def resume(self):
        """
        Method used to resume the use of the provided `url` and `header` values.
        The `header` values are expected to include the previous values as provided
        from the use of the :meth:`login`.

        Raises:
            - LoginServerUnreachableError: when the probe of AOS server fails
            - LoginError: unable to get the version information
            - LoginAuthError: the `headers` do not contain valid token
        """

        if not self.probe():
            raise LoginServerUnreachableError(
                message="Trying URL: [{}]".format(self.url))

        if not self.verify_token():
            raise LoginAuthError()

        self.get_ver()

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
        rsp = self.requests.post(
            "%s/user/login" % self.url,
            json=dict(username=user, password=passwd))

        if not rsp.ok:
            raise LoginAuthError()

        self.token = rsp.json()['token']
        self.get_ver()

    def get_ver(self):
        """
        Used to retrieve the AOS API version information.

        Raises:
            - ValueError: the retrieve version string is not semantically valid
        """
        got = self.requests.get("%s/versions/api" % self.url)
        self.version = copy(got.json())

        try:
            self.version['semantic'] = semantic_version.Version(self.version['version'])
        except ValueError:
            self.version['semantic'] = semantic_version.Version(self.version['version'], partial=True)

        return self.version

    def verify_token(self):
        """
        This method is used to verify that the existing AUTHTOKEN is still valid.
        Given that there is currently not a specific API for this, going to use
        the "get user" API as a test-point.

        Returns:
            - True if able to access API with auth headers
            - False otherwise
        """
        return self.requests.get('%s/user' % self.url).ok

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
