
# : we recommend that you connect to Redis via Twemproxy
stream_framework_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}

stream_framework_CASSANDRA_HOSTS = ['localhost']

stream_framework_DEFAULT_KEYSPACE = 'stream_framework'

stream_framework_CASSANDRA_CONSISTENCY_LEVEL = None

stream_framework_CASSANDRA_READ_RETRY_ATTEMPTS = 1

stream_framework_CASSANDRA_WRITE_RETRY_ATTEMPTS = 1

CASSANDRA_DRIVER_KWARGS = {}

stream_framework_METRIC_CLASS = 'stream_framework.metrics.base.Metrics'

stream_framework_METRICS_OPTIONS = {}

stream_framework_VERB_STORAGE = 'in-memory'

try:
    from cassandra import ConsistencyLevel
    stream_framework_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
