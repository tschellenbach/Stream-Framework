from stream_framework.storage.redis.connection import get_redis_connection
from redis.client import BasePipeline


class RedisCache(object):

    '''
    The base for all redis data structures
    '''
    key_format = 'redis:cache:%s'

    def __init__(self, key, redis=None, redis_server='default'):
        # write the key
        self.key = key
        # handy when using fallback to other data sources
        self.source = 'redis'
        # the redis connection, self.redis is lazy loading the connection
        self._redis = redis
        # the redis server (see get_redis_connection)
        self.redis_server = redis_server

    def get_redis(self):
        '''
        Only load the redis connection if we use it
        '''
        if self._redis is None:
            self._redis = get_redis_connection(
                server_name=self.redis_server
            )
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

    def _pipeline_if_needed(self, operation, *args, **kwargs):
        '''
        If the redis connection is already in distributed state use it
        Otherwise spawn a new distributed connection using .map
        '''
        pipe_needed = not isinstance(self.redis, BasePipeline)
        if pipe_needed:
            pipe = self.redis.pipeline(transaction=False)
            operation(pipe, *args, **kwargs)
            results = pipe.execute()
        else:
            results = operation(self.redis, *args, **kwargs)
        return results
