from cqlengine import connection
from feedly import settings


def setup_connection():
    connection.setup(
        settings.FEEDLY_CASSANDRA_HOSTS,
        consistency=settings.FEEDLY_CASSANDRA_CONSISTENCY_LEVEL,
        default_keyspace=settings.FEEDLY_DEFAULT_KEYSPACE,
        metrics_enabled=settings.FEEDLY_TRACK_CASSANDRA_DRIVER_METRICS,
        default_timeout=settings.FEEDLY_CASSANDRA_DEFAULT_TIMEOUT
    )
