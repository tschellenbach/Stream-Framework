
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

FEEDLY_DEFAULT_KEYSPACE = 'feedly'

FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = None

FEEDLY_TRACK_METRICS = False

FEEDLY_METRIC_CLASS = 'feedly.metrics.statsd.StatsdMetrics'

FEEDLY_METRICS_OPTIONS = {
	'host': 'localhost',
	'port': 8125,
	'prefix': 'feedly'
}

try:
    from cassandra import ConsistencyLevel
    FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
