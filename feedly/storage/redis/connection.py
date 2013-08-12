# cache this at the process module level
connection_cache = {}


from feedly import settings


def get_redis_connection():
    from nydus.db import create_cluster
    config = settings.FEEDLY_NYDUS_CONFIG['CONNECTIONS']['redis']
    key = unicode(config)
    cluster = connection_cache.get(key)
    if not cluster:
        cluster = create_cluster(config)
        connection_cache[key] = cluster
    return cluster
