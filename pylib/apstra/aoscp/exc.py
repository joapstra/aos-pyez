# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


class LoginError(Exception):
    pass


class LoginNoServerError(LoginError):
    pass


class LoginServerUnreachableError(LoginError):
    pass


class SessionError(Exception):
    pass


class SessionRqstError(SessionError):
    def __init__(self, response):
        self.response = response
        super(SessionRqstError, self).__init__()