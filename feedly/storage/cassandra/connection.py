from cqlengine import connection
from feedly import settings


def setup_connection():
    connection.setup(
        settings.FEEDLY_CASSANDRA_HOSTS,
        consistency=settings.FEEDLY_CASSANDRA_CONSISTENCY_LEVEL,
        default_keyspace=settings.FEEDLY_DEFAULT_KEYSPACE
    )
