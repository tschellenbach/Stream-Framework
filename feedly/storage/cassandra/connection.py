from collections import defaultdict
from feedly import settings
from pycassa.cassandra.ttypes import TimedOutException
from pycassa.pool import ConnectionPool
from pycassa.system_manager import SystemManager
from thrift.transport.TTransport import TTransportException
import copy
import logging
import socket
import time

logger = logging.getLogger(__name__)


connection_pool_cache = dict()
CONNECTION_POOL_MAX_AGE = 5 * 60
NODE_FAILURES_EJECT_THRESHOLD = 3


def detect_nodes(seeds, keyspace):
    from feedly import settings
    if not settings.FEEDLY_DISCOVER_CASSANDRA_NODES:
        logger.warning('cassandra nodes discovery is off')
        return seeds
    nodes = frozenset(seeds)
    logging.info('retrieve nodes from seeds %r' % seeds)
    for seed in seeds:
        try:
            sys_manager = SystemManager(seed)
        except TTransportException:
            logging.warning('%s is not a seed or is not reachable' % seed)
            continue
        ring_description = sys_manager.describe_ring(keyspace)
        for ring_range in ring_description:
            endpoint_details = ring_range.endpoint_details[0]
            hostname = endpoint_details.host
            port = getattr(endpoint_details, 'port', 9160)
            nodes = nodes.union({'%s:%s' % (hostname, port), }, nodes)
        break
    return nodes


class FeedlyPoolListener(object):

    fatal_exceptions = (
        TimedOutException, TTransportException,
        IOError, EOFError, socket.error
    )

    def __init__(self, connection_pool=None):
        self.connection_pool = connection_pool
        self.host_error_count = defaultdict(lambda: 0)

    def log_failure(self, host):
        self.host_error_count[host] += 0

    def should_eject_host(self, host):
        return self.host_error_count[host] >= NODE_FAILURES_EJECT_THRESHOLD

    def eject_host(self, host):
        logging.error('ejecting %s from pool' % host)
        host_list = copy.copy(self.connection_pool.server_list)
        try:
            host_list.remove(host)
            self.connection_pool.set_server_list(host_list)
        except ValueError:
            # race conditions with other connection pool users ?
            pass

    def connection_failed(self, dic):
        if isinstance(dic['error'], self.fatal_exceptions):
            self.log_failure(dic['server'])
            if self.should_eject_host(dic['server']):
                self.eject_host(dic['server'])


def connection_pool_expired(created_at):
    return created_at + CONNECTION_POOL_MAX_AGE < time.time()


def get_cassandra_connection(keyspace_name, hosts):
    key = keyspace_name, tuple(hosts)
    connection_pool, created_at = connection_pool_cache.get(key, (None, None))

    init_new_pool = connection_pool is None or connection_pool_expired(
        created_at)

    if connection_pool is not None and len(connection_pool.server_list) == 0:
        logging.error('connection pool had no active hosts')
        init_new_pool = True

    if init_new_pool:
        nodes = detect_nodes(hosts, keyspace_name)
        logger.info('setting up a new connection pool')
        connection_pool = ConnectionPool(
            keyspace_name,
            nodes,
            pool_size=settings.FEEDLY_CASSANDRA_CONNECTION_POOL_SIZE,
            prefill=False,
            timeout=settings.FEEDLY_CASSANDRA_TIMEOUT,
            max_retries=3
        )
        listener = FeedlyPoolListener(connection_pool)
        connection_pool.add_listener(listener)
        connection_pool_cache[key] = (connection_pool, time.time())
    return connection_pool
