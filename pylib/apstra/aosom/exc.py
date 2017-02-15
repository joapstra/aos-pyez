# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


# ##### ---------------------------------------------------
# ##### Parent Exception class for everything
# ##### ---------------------------------------------------

class AosOmError(Exception):
    def __init__(self, message=None):
        super(AosOmError, self).__init__(message)


# ##### ---------------------------------------------------
# ##### Login related exceptions
# ##### ---------------------------------------------------

class LoginError(AosOmError):
    def __init__(self, message=None):
        super(LoginError, self).__init__(
            message or 'AOS-server login error')


class LoginNoServerError(LoginError):
    def __init__(self, message=None):
        super(LoginNoServerError, self).__init__(
            message or 'AOS-server value not provided')


class LoginServerUnreachableError(LoginError):
    def __init__(self, message=None):
        super(LoginServerUnreachableError, self).__init__(
            message or 'AOS-server unreachable')


class LoginAuthError(LoginError):
    def __init__(self, message=None):
        super(LoginAuthError, self).__init__(
            message or 'AOS-server invalid auth credentials')


class NoLoginError(LoginError):
    def __init__(self, message=None):
        super(NoLoginError, self).__init__(
            message or 'AOS-server no valid session')


# ##### ---------------------------------------------------
# ##### Session processing exceptions
# ##### ---------------------------------------------------

class SessionError(AosOmError):
    def __init__(self, message=None):
        super(SessionError, self).__init__(message)


class SessionRqstError(SessionError):
    def __init__(self, resp, message=None):
        self.resp = resp
        emsg = '{}:{}'.format(resp.status_code, resp.text)
        emsg = emsg + ' - %s' % message if message else emsg
        super(SessionRqstError, self).__init__(emsg)


class AccessValueError(SessionError):
    def __init__(self, message=None):
        super(AccessValueError, self).__init__(message)


class NoExistsError(SessionError):
    """
    Attempting to take action on an item when it does not exist.
    """
    def __init__(self, message=None):
        super(NoExistsError, self).__init__(message)


class DuplicateError(SessionError):
    """
    Attempting to take action that would result in a duplicate;
    for example creating something that already exists
    """
    def __init__(self, message=None):
        super(DuplicateError, self).__init__(message)
