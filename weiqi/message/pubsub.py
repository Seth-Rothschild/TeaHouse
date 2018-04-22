import json
from collections import defaultdict


class PubSub:
    def __init__(self, broker):
        self._broker = broker
        self._broker.add_handler(self._on_message)

        self._subs = defaultdict(set)

    def _on_message(self, message):
        message = json.loads(message)
        topic = message.get('topic')
        data = message.get('data')

        for sub in self._subs[topic]:
            sub(topic, data)

    def publish(self, topic, data):
        message = json.dumps({
            'topic': topic,
            'data': data
        })

        self._broker.send_message(message)

    def subscribe(self, topic, handler):
        self._subs[topic].add(handler)

    def unsubscribe(self, topic, handler):
        self._subs[topic].remove(handler)

    def close(self):
        self._broker.remove_handler(self._on_message)
