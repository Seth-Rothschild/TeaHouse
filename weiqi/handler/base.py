from tornado.web import RequestHandler
from weiqi import settings
from weiqi.db import session
from weiqi.models import User


class BaseHandler(RequestHandler):
    def initialize(self, pubsub):
        self.pubsub = pubsub

    def get_current_user(self):
        id = self.get_secure_cookie(settings.COOKIE_NAME)

        if not id:
            return None

        if not self.db.query(User).get(int(id)):
            return None

        return int(id)

    def query_current_user(self):
        return self.db.query(User).get(self.current_user)

    def enable_cors(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", 'GET')

    def _execute(self, *args, **kwargs):
        with session() as db:
            self.db = db
            super()._execute(*args, **kwargs)
