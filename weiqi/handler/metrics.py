from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest
from weiqi.handler.base import BaseHandler


class MetricsHandler(BaseHandler):
    def get(self):
        self.set_header('Content-Type', CONTENT_TYPE_LATEST)
        self.write(generate_latest())
