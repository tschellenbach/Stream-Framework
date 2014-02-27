
# : we recommend that you connect to Redis via Twemproxy
FEEDLY_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}

FEEDLY_CASSANDRA_HOSTS = ['localhost']

FEEDLY_CASSANDRA_DEFAULT_TIMEOUT = 10.0

FEEDLY_DEFAULT_KEYSPACE = 'feedly'

FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = None

FEEDLY_CASSANDRA_READ_RETRY_ATTEMPTS = 1

FEEDLY_CASSANDRA_WRITE_RETRY_ATTEMPTS = 1

FEEDLY_TRACK_CASSANDRA_DRIVER_METRICS = False

FEEDLY_METRIC_CLASS = 'feedly.metrics.base.Metrics'

FEEDLY_METRICS_OPTIONS = {}

FEEDLY_VERB_STORAGE = 'in-memory'

try:
    from cassandra import ConsistencyLevel
    FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
