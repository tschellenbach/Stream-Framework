from feedly import get_redis_connection
from nydus.db.base import DistributedConnection


class RedisCache(object):
    '''
    The base for all redis data structures
    '''
    key_format = 'redis:cache:%s'

    def __init__(self, key_data, redis=None):
        #write the key
        self.key_data = key_data
        self.key = self.key_format % key_data
        #handy when using fallback to other data sources
        self.source = 'redis'
        #the redis connection
        self.redis = redis or get_redis_connection()

    def get_key(self):
        return self.key

    def delete(self):
        key = self.get_key()
        self.redis.delete(key)

    def _map_if_needed(self, operation, *args, **kwargs):
        '''
        If the redis connection is already in distributed state use it
        Otherwise spawn a new distributed connection using .map
        '''
        map_needed = not isinstance(self.redis, DistributedConnection)
        if map_needed:
            with self.redis.map() as redis:
                results = operation(redis, *args, **kwargs)
        else:
            results = operation(self.redis, *args, **kwargs)
        return results
    
    def map(self):
        return InternalMap(self)


class InternalMap(object):
    '''
    Context manager temporarily use map from within the class
    It temporarily overwrites self.redis for the cache_class
    '''
    def __init__(self, cache_class):
        self.redis = cache_class.redis
        self.redis_map = cache_class.redis.map()
        self.cache_class = cache_class
        
    def __enter__(self):
        self.cache_class.redis = self.redis_map.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redis_map.__exit__(exc_type, exc_val, exc_tb)
        self.cache_class.redis = self.redis

