# cache this at the process module level
connection_cache = {}


NYDUS_CONFIG = {
        'CONNECTIONS': {
            'redis': {
                'engine': 'nydus.db.backends.redis.Redis',
                'router': 'nydus.db.routers.redis.PrefixPartitionRouter',
                'hosts': {
                    0: {'prefix': 'default', 'db': 0, 'host': 'default.redis.goteam.be', 'port': 6379},
                    12: {'prefix': 'feedly:', 'db': 0, 'host': 'feedly1.redis.goteam.be', 'port': 6379},
                    13: {'prefix': 'feedly:', 'db': 1, 'host': 'feedly2.redis.goteam.be', 'port': 6379},
                }
            },
        }
}


def get_redis_connection():
    from nydus.db import create_cluster
    config = NYDUS_CONFIG['CONNECTIONS']['redis']
    key = unicode(config)
    cluster = connection_cache.get(key)
    if not cluster:
        cluster = create_cluster(config)
        connection_cache[key] = cluster
    return cluster
