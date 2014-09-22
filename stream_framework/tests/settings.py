import os

FEEDLY_DEFAULT_KEYSPACE = 'test_feedly'

if os.environ.get('TEST_CASSANDRA_HOST'):
    FEEDLY_CASSANDRA_HOSTS = [os.environ['TEST_CASSANDRA_HOST']]

SECRET_KEY = 'ib_^kc#v536)v$x!h3*#xs6&l8&7#4cqi^rjhczu85l9txbz+w'
FEEDLY_DISCOVER_CASSANDRA_NODES = False
FEEDLY_CASSANDRA_CONSITENCY_LEVEL = 'ONE'


FEEDLY_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}
