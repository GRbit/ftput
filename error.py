class FTPException(Exception):
    def __init__(self, err):
        print('FTP authentification Exception: ', err)


class FileUnavailable(Exception):
    def __init__(self, err):
        print('FTP file unavailable Exception: ', err)


class AuthError(Exception):
    def __init__(self, err):
        print('FTP authentification Exception: ', err)


class ImpossiburuAnswer(Exception):
    def __init__(self, err):
        print('ImpossiburuAnswer Exception: ', err)
