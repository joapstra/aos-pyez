# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


# ##### ---------------------------------------------------
# ##### Parent Exception class for everything
# ##### ---------------------------------------------------

class AosCpError(Exception):
    def __init__(self, message=None, **kwargs):
        super(AosCpError, self).__init__(message)

# ##### ---------------------------------------------------
# ##### Login related exceptions
# ##### ---------------------------------------------------

class LoginError(AosCpError):
    def __init__(self, message=None, **kwargs):
        super(self.__class__, self).__init__(message, **kwargs)


class LoginNoServerError(LoginError):
    def __init__(self, message=None, **kwargs):
        super(self.__class__, self).__init__(
            message or 'AOS-server value not provided', **kwargs)


class LoginServerUnreachableError(LoginError):
    def __init__(self, message=None, **kwargs):
        super(self.__class__, self).__init__(
            message or 'AOS-server unreachable', **kwargs)


class LoginAuthError(LoginError):
    def __init__(self, message=None, **kwargs):
        super(self.__class__, self).__init__(
            message or 'AOS-server authentication error', **kwargs)

# ##### ---------------------------------------------------
# ##### Session processing exceptions
# ##### ---------------------------------------------------

class SessionError(AosCpError):
    def __init__(self, message=None, **kwargs):
        super(SessionError, self).__init__(message, **kwargs)


class SessionRqstError(SessionError):
    def __init__(self, resp, message=None, **kwargs):
        self.resp = resp
        super(SessionRqstError, self).__init__(message, **kwargs)


class AccessValueError(SessionError):
    def __init__(self, message=None, **kwargs):
        super(AccessValueError, self).__init__(message, **kwargs)
