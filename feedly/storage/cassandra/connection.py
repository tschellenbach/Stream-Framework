from pycassa.pool import ConnectionPool
from feedly.utils.local import Local
import logging

logger = logging.getLogger(__name__)

local = Local()


def get_cassandra_connection(keyspace_name, hosts):
    if local._connection is None:
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
        local._connection = connection_pool
    return local._connection

local._connection = None
