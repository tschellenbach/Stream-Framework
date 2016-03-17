import os

STREAM_DEFAULT_KEYSPACE = 'test_stream_framework'

if os.environ.get('TEST_CASSANDRA_HOST'):
    STREAM_CASSANDRA_HOSTS = [os.environ['TEST_CASSANDRA_HOST']]

SECRET_KEY = 'ob_^kc#v536)v$x!h3*#xs6&l8&7#4cqi^rjhczu85l9txbz+W'
STREAM_CASSANDRA_CONSITENCY_LEVEL = 'ONE'


STREAM_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}
