
FEEDLY_REDIS_CONFIG = {
    'default': {
        'host': 'locahost',
        'port': 6379,
        'db': 0
    },
}

FEEDLY_CASSANDRA_HOSTS = ['localhost']

FEEDLY_DEFAULT_KEYSPACE = 'feedly'

FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = None

try:
    from cassandra import ConsistencyLevel
    FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
