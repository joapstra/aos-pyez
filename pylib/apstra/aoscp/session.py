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

from apstra.aoscp.exc import *


class Session(object):
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

    def __init__(self, **kwargs):
        self.api_headers = {}
        self.api_http = None
        self.token = None
        self.server = None
        self.port = None
        self.user = None
        self.passwd = None

        self.set_login(**kwargs)

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PUBLIC METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def set_login(self, **kwargs):
        self.token = kwargs.get('token') or os.getenv(Session._ENV['TOKEN'])

        self.server = kwargs.get('server') or os.getenv(Session._ENV['SERVER'])

        self.port = kwargs.get('port') \
                    or os.getenv(Session._ENV['PORT']) or Session._DEFAULTS['PORT']

        self.user = kwargs.get('user') \
                    or os.getenv(Session._ENV['USER']) or Session._DEFAULTS['USER']

        self.passwd = kwargs.get('passwd') \
                      or os.getenv(Session._ENV['PASSWD']) or Session._DEFAULTS['PASSWD']


    def accept_token(self, token):
        self.token = token
        self.api_headers['AUTHTOKEN'] = self.token

    def login(self):
        self.api_http = "http://{server}:{port}/api".format(
            server=self.server, port=self.port)

        if not self.server:
            raise LoginNoServerError()

        if not self.probe():
            raise LoginServerUnreachableError()

        rsp = requests.post(
            "%s/user/login" % self.api_http,
            json=dict(username=self.user, password=self.passwd))

        if not rsp.ok:
            raise SessionRqstError(rsp)

        self.accept_token(rsp.json()['token'])

    def probe(self, timeout=5, intvtimeout=1):
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
