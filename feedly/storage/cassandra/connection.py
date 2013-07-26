from pycassa.pool import ConnectionPool
import logging

logger = logging.getLogger(__name__)


connection_pool_cache = dict()


def get_cassandra_connection(keyspace_name, hosts):
    key = keyspace_name, tuple(hosts)
    connection_pool = connection_pool_cache.get(key)
    if connection_pool is None:
        logger.info('setting up the connection pool')
        pool_size = len(hosts) * 24
        connection_pool = ConnectionPool(
            keyspace_name,
            hosts,
            pool_size=pool_size,
            prefill=False,
            timeout=10,
            max_retries=3
        )
        connection_pool_cache[key] = connection_pool
    return connection_pool
