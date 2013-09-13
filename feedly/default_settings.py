FEEDLY_NYDUS_CONFIG = {
    'CONNECTIONS': {
        'redis': {
            'engine': 'nydus.db.backends.redis.Redis',
            'router': 'nydus.db.routers.redis.PrefixPartitionRouter',
            'hosts': {
                0: {'prefix': 'default', 'db': 0, 'host': 'localhost', 'port': 6379},
            }
        },
    }
}

FEEDLY_CASSANDRA_HOSTS = ['localhost']

FEEDLY_DEFAULT_KEYSPACE = 'feedly'

FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = None

try:
    from cassandra import ConsistencyLevel
    FEEDLY_CASSANDRA_CONSISTENCY_LEVEL = ConsistencyLevel.ONE
except ImportError:
    pass
