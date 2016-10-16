# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


class AosCpError(Exception):
    def __init__(self, *vargs, **kwargs):
        super(AosCpError, self).__init__(*vargs, **kwargs)





class LoginError(AosCpError):
    def __init__(self, *vargs, **kwargs):
        super(LoginError, self).__init__(*vargs, **kwargs)


class LoginNoServerError(LoginError):
    def __init__(self, *vargs, **kwargs):
        super(LoginNoServerError, self).__init__(*vargs, **kwargs)


class LoginServerUnreachableError(LoginError):
    def __init__(self, *vargs, **kwargs):
        super(LoginServerUnreachableError, self).__init__(*vargs, **kwargs)


class LoginAuthError(LoginError):
    def __init__(self, *vargs, **kwargs):
        super(LoginAuthError, self).__init__(*vargs, **kwargs)


class SessionError(AosCpError):
    def __init__(self, *vargs, **kwargs):
        super(SessionError, self).__init__(*vargs, **kwargs)


class SessionRqstError(SessionError):
    def __init__(self, resp, *vargs, **kwargs):
        super(SessionRqstError, self).__init__(*vargs, **kwargs)
        self.resp = resp


class AccessValueError(SessionError):
    def __init__(self, *vargs, **kwargs):
        super(AccessValueError, self).__init__(*vargs, **kwargs)