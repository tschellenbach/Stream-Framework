from feedly.storage.redis.connection import get_redis_connection
from nydus.db.base import DistributedConnection


class RedisCache(object):

    '''
    The base for all redis data structures
    '''
    key_format = 'redis:cache:%s'

    def __init__(self, key, redis=None):
        # write the key
        self.key = key
        # handy when using fallback to other data sources
        self.source = 'redis'
        # the redis connection, self.redis is lazy loading the connection
        self._redis = redis

    def get_redis(self):
        '''
        Only load the redis connection if we use it
        '''
        if self._redis is None:
            self._redis = get_redis_connection()
        return self._redis

    def set_redis(self, value):
        '''
        Sets the redis connection
        '''
        self._redis = value

    redis = property(get_redis, set_redis)

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
