from pycassa.pool import ConnectionPool
from feedly.utils.local import Local
import logging

logger = logging.getLogger(__name__)

local = Local()


def get_cassandra_connection(keyspace_name, hosts):
    connection_pool = getattr(local, '_connection_pool', None)
    if connection_pool is None:
        logger.info('setting up the connection pool')
        pool_size = len(hosts) * 24
        connection_pool = ConnectionPool(
            keyspace_name,
            hosts,
            pool_size=pool_size,
            prefill=False,
            timeout=3,
            max_retries=2
        )
        local._connection_pool = connection_pool
    return connection_pool

local._connection = None
