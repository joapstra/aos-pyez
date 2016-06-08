
class LoginError(Exception):
    pass


class LoginNoServerError(LoginError):
    pass


class LoginServerUnreachableError(LoginError):
    pass
