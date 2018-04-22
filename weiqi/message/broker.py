import pika
from pika import adapters
from weiqi import settings


class Ampq:
    """Implements a client for the Advanced Message Queuing Protocol (AMPQ) which can be used to connect to RabbitMQ."""
    EXCHANGE = 'weiqi'
    EXCHANGE_TYPE = 'fanout'

    def __init__(self, ampq_url):
        self._connection = None
        self._channel = None
        self._queue = None
        self._queue_name = None
        self._consumer_tag = None
        self._closing = False
        self._url = ampq_url
        self._handler = set()

    def run(self):
        self._connection = self.connect()

    def connect(self):
        return adapters.TornadoConnection(pika.URLParameters(self._url), self.on_connection_open)

    def close(self):
        self._connection.close()

    def on_connection_open(self, conn):
        self._connection.add_on_close_callback(self.on_connection_closed)
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self._channel.exchange_declare(
            self.on_exchange_declareok, self.EXCHANGE, self.EXCHANGE_TYPE)

    def on_exchange_declareok(self, frame):
        self._queue = self._channel.queue_declare(
            self.on_queue_declareok, exclusive=True)

    def on_queue_declareok(self, frame):
        self._queue_name = frame.method.queue
        self._channel.queue_bind(
            self.on_bindok, exchange=self.EXCHANGE, queue=self._queue_name)

    def on_bindok(self, frame):
        self._consumer_tag = self._channel.basic_consume(
            self.on_message, queue=self._queue_name)

    def on_message(self, channel, basic_deliver, properties, body):
        self._channel.basic_ack(basic_deliver.delivery_tag)

        body = body.decode()
        for handler in self._handler:
            handler(body)

    def send_message(self, message):
        self._channel.basic_publish(
            exchange=self.EXCHANGE, routing_key='', body=message)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self._connection.close()

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if not self._closing:
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        if not self._closing:
            self._connection = self.connect()

    def stop(self):
        self._closing = True

        if self._channel:
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self):
        self._channel.close()

    def add_handler(self, handler):
        self._handler.add(handler)

    def remove_handler(self, handler):
        self._handler.remove(handler)


class DummyBroker:
    """Implements a dummy message broker client.

    This implementation simply broadcasts all messages to all handlers and works only within the same process.
    This can be used for tests and/or for development.
    """

    def __init__(self):
        self._handler = set()

    def run(self):
        pass

    def add_handler(self, handler):
        self._handler.add(handler)

    def remove_handler(self, handler):
        self._handler.remove(handler)

    def send_message(self, message):
        for handler in self._handler:
            handler(message)


def create_message_broker():
    """Creates a new message broker instance based on the `weiqi.settings.MESSAGE_BROKER` setting."""
    if settings.MESSAGE_BROKER == 'ampq':
        return Ampq(settings.AMPQ_URL)
    else:
        return DummyBroker()
