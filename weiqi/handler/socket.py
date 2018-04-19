import json
import logging
import uuid

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler
from weiqi import settings, metrics
from weiqi.db import session
from weiqi.models import User
from weiqi.services import ConnectionService, execute_service


class SocketMixin:
    def initialize(self, pubsub):
        self.id = str(uuid.uuid4())
        self.pubsub = pubsub
        self._subs = set()

    def get_compression_options(self):
        return {}

    def open(self):
        with session() as db:
            user = self._get_user(db)
            ConnectionService(db, self, user).connect()

        metrics.CONNECTED_SOCKETS.inc()

    def on_message(self, data):
        msg = json.loads(data)
        service, method = msg.get('method').split('/', 1)

        with metrics.REQUEST_TIME.labels(msg.get('method')).time():
            IOLoop.current().add_callback(self._execute_service, service,
                                          method, msg.get('data'), msg.get('id'))

    def on_close(self):
        for topic in self._subs:
            self.pubsub.unsubscribe(topic, self._on_pubsub)

        with session() as db:
            user = self._get_user(db)
            ConnectionService(db, self, user).disconnect()

        metrics.CONNECTED_SOCKETS.dec()

    def subscribe(self, topic):
        if topic not in self._subs:
            self.pubsub.subscribe(topic, self._on_pubsub)
            self._subs.add(topic)

    def unsubscribe(self, topic):
        if topic in self._subs:
            self.pubsub.unsubscribe(topic, self._on_pubsub)
            self._subs.remove(topic)

    def is_subscribed(self, topic):
        return topic in self._subs

    def publish(self, topic, data):
        self.pubsub.publish(topic, data)

    def send(self, topic, data):
        self._send_data({'method': topic, 'data': data})

    def _send_data(self, data, response_to=''):
        method = data.get(
            'method') if not response_to else 'response/' + response_to
        data = json.dumps(data)

        metrics.SENT_MESSAGES.labels(method).observe(len(data))

        self.write_message(data)

    def _on_pubsub(self, topic, data):
        topic = topic.split('/')[0]
        self.send(topic, data)

    @gen.coroutine
    def _execute_service(self, service, method, data=None, id=None):
        user_id = self.get_secure_cookie(settings.COOKIE_NAME)
        user_id = int(user_id) if user_id else None
        res = yield execute_service(self, user_id, service, method, data)

        if id is not None:
            self._send_data({'method': 'response', 'id': id,
                             'data': res}, response_to=service + '/' + method)

    def _get_user(self, db):
        user_id = self.get_secure_cookie(settings.COOKIE_NAME)
        user = db.query(User).get(int(user_id)) if user_id else None
        return user


class SocketHandler(SocketMixin, WebSocketHandler):
    def _execute_service(self, *args, **kwargs):
        try:
            return super()._execute_service(*args, **kwargs)
        except:
            logging.exception('service failed to execute')
