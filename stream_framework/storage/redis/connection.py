import redis
from stream_framework import settings

connection_pool = None


def get_redis_connection(server_name='default'):
    '''
    Gets the specified redis connection
    '''
    global connection_pool

    if connection_pool is None:
        connection_pool = setup_redis()

    pool = connection_pool[server_name]

    return redis.StrictRedis(connection_pool=pool)


def setup_redis():
    '''
    Starts the connection pool for all configured redis servers
    '''
    pools = {}
    for name, config in settings.STREAM_REDIS_CONFIG.items():
        pool = redis.ConnectionPool(
            host=config['host'],
            port=config['port'],
            password=config.get('password'),
            db=config['db'],
            decode_responses=config.get('decode_responses', True),
            # connection options
            socket_timeout=config.get('socket_timeout', None),
            socket_connect_timeout=config.get('socket_connect_timeout', None),
            socket_keepalive=config.get('socket_keepalive', False),
            socket_keepalive_options=config.get('socket_keepalive_options', None),
            retry_on_timeout=config.get('retry_on_timeout', False),
        )
        pools[name] = pool
    return pools
