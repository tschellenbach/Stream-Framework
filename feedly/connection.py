from nydus.db import create_cluster

#cache this at the process module level
connection_cache = {}


def get_redis_connection():
    from django.conf import settings
    config = settings.NYDUS_CONFIG['CONNECTIONS']['redis']
    key = unicode(config)
    cluster = connection_cache.get(key)
    if not cluster:
        cluster = create_cluster(config)
        connection_cache[key] = cluster
    return cluster
