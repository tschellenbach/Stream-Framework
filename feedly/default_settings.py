FEEDLY_REDIS_HOST = 'locahost'
FEEDLY_REDIS_PORT = 6379
FEEDLY_REDIS_DB = 0

FEEDLY_REDIS_CONFIG = {
    'host': FEEDLY_REDIS_HOST,
    'port': FEEDLY_REDIS_PORT,
    'db': FEEDLY_REDIS_DB
}

FEEDLY_CASSANDRA_HOSTS = ['localhost']

# if True detects the nodes by querying the cassandra seeds
FEEDLY_DISCOVER_CASSANDRA_NODES = True
# timeout before giving up upon requests
FEEDLY_CASSANDRA_TIMEOUT = 0.75

FEEDLY_DEFAULT_KEYSPACE = 'feedly'

FEEDLY_CASSANDRA_CONSITENCY_LEVEL = 'ONE'
