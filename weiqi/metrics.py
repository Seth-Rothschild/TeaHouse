from prometheus_client import Summary, Gauge, Counter


REQUEST_TIME = Summary('weiqi_request_processing_seconds',
                       'Time spent processing requests', ['method'])
SENT_MESSAGES = Summary('weiqi_sent_message_bytes',
                        'Size of outgoing messages', ['method'])
CONNECTED_SOCKETS = Gauge('weiqi_connected_sockets',
                          'Number of connected websockets')
EXCEPTIONS = Counter('weiqi_exceptions_total',
                     'Number of exceptions in requests', ['method'])
REGISTRATIONS = Counter('weiqi_registrations_total',
                        'Total number of registrations')
