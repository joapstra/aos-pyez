
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

    def __init__(self, **kwargs):
        self.api_headers = {}
        self.api_http = None
        self.set_login(kwargs)

    def set_login(self, **kwargs):
        self.token = kwargs.get('token') or os.getenv(Session._ENV['TOKEN'])
        self.server = kwargs.get('server') or os.getenv(Session._ENV['SERVER'])
        self.port = kwargs.get('port') or os.getenv(Session._ENV['PORT'])
        self.user = kwargs.get('user') or os.getenv(Session._ENV['USER'])
        self.passwd = kwargs.get('passwd') or os.getenv(Session._ENV['PASSWD'])

        self.api_http = "http://{server}:{port}/api".format(
            server=self.server, port=self.port)

        self.api_headers['authorization'] = self.token

    # ### ---------------------------------------------------------------------
    # ###
    # ###                         PUBLIC METHODS
    # ###
    # ### ---------------------------------------------------------------------

    def login(self):
        if not self.server:
            raise LoginNoServerError()

        if not self.probe():
            raise LoginServerUnreachableError()


    def authenticate(self, user, passwd):
        got = self.sign_in(user, passwd)
        if not got.ok:
            # try to see if this is a first-time login
            first_timer = self.sign_in(user, self.NOPASSWD)
            err = AosLoginAuthFirstError \
                if 403 == first_timer.status_code else AosLoginAuthError
            raise err()

        self.token = got.json()['session_token']

    def validate_token(self, token):
        tmp_hdrs = copy(self.headers)
        tmp_hdrs['authorization'] = token

        got = requests.get(
            "%s/session_test" % self.http_api,
            headers=tmp_hdrs)

        return got.ok

    def sign_in(self, user, passwd):
        return requests.post(
            '%s/sign-in' % self.http_api,
            json={
                "user_name": user,
                "user_password": passwd
            })

    def probe(self, timeout=5, intvtimeout=1):
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=timeout)
        hostname, port = self.server.split(':')

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(intvtimeout)
            try:
                s.connect((hostname, int(port)))
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                return True
            except:
                time.sleep(1)
                pass
        else:
            # elapsed = datetime.datetime.now() - start
            return False

