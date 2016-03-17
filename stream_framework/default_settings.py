
# : we recommend that you connect to Redis via Twemproxy
STREAM_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}

STREAM_CASSANDRA_HOSTS = ['localhost']

STREAM_DEFAULT_KEYSPACE = 'stream_framework'

STREAM_CASSANDRA_CONSISTENCY_LEVEL = None

STREAM_CASSANDRA_READ_RETRY_ATTEMPTS = 1

STREAM_CASSANDRA_WRITE_RETRY_ATTEMPTS = 1

CASSANDRA_DRIVER_KWARGS = {
    'protocol_version': 2
}

STREAM_METRIC_CLASS = 'stream_framework.metrics.base.Metrics'

STREAM_METRICS_OPTIONS = {}

STREAM_VERB_STORAGE = 'in-memory'

try:
    from cassandra import ConsistencyLevel
    STREAM_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
