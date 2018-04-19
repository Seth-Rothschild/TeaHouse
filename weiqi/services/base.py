from tornado.web import HTTPError


class ServiceError(Exception):
    pass


class BaseService:
    _methods = {}

    def __init__(self, db=None, socket=None, user=None):
        self.db = db
        self.socket = socket
        self.user = user

    @classmethod
    def register(cls, func):
        """Registers a method to be used via the `execute` method."""
        cls._methods[func.__qualname__] = func
        return func

    @classmethod
    def authenticated(cls, func):
        def inner(self, *args, **kwargs):
            if not self.user:
                raise HTTPError(403)
            return func(self, *args, **kwargs)
        return inner

    def execute(self, method, data=None):
        """Executes the given method on this class.

        The method name has to be registered via the `register` decorator.
        """
        method = self.__class__.__name__ + '.' + method

        if method not in self._methods:
            raise ServiceError('invalid method "{}"'.format(method))

        return self._methods[method](self, **(data or {}))
