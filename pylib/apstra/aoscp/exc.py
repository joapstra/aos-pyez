# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


class AosCpError(Exception):
    pass


class LoginError(AosCpError):
    pass


class LoginNoServerError(LoginError):
    pass


class LoginServerUnreachableError(LoginError):
    pass


class LoginAuthError(LoginError):
    pass


class SessionError(AosCpError):
    pass


class SessionRqstError(SessionError):
    def __init__(self, resp):
        super(SessionRqstError, self).__init__()
        self.resp = resp
