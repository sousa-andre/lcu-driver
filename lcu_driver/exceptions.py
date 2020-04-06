class PlatformNotSupported(BaseException):
    pass


class IntegrityError(BaseException):
    pass


class CoroutineExpected(BaseException):
    def __init__(self, coroutine_name):
        super().__init__(f'a coroutine was expected, replace "def {coroutine_name}" by "async def {coroutine_name}"')


class EarlyPerform(BaseException):
    pass


class InvalidURI(BaseException):
    def __init__(self, error_type, used_uri=None):
        if error_type == 'backslash':
            super().__init__(f'every endpoint must start with a backslash, replace {used_uri} by /{used_uri}')
