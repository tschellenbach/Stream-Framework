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
