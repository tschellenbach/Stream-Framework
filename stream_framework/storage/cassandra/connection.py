from cqlengine import connection
from stream_framework import settings


def setup_connection():
    connection.setup(
        hosts=settings.stream_framework_CASSANDRA_HOSTS,
        consistency=settings.stream_framework_CASSANDRA_CONSISTENCY_LEVEL,
        default_keyspace=settings.stream_framework_DEFAULT_KEYSPACE,
        **settings.CASSANDRA_DRIVER_KWARGS
    )
