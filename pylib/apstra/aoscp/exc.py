
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