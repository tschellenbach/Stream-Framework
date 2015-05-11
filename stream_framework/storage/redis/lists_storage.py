from stream_framework.storage.base_lists_storage import BaseListsStorage
from stream_framework.storage.redis.connection import get_redis_connection

import six


class RedisListsStorage(BaseListsStorage):

    def _to_result(self, results):
        if results:
            if len(results) == 1:
                return results[0]
            else:
                return tuple(results)

    @property
    def redis(self):
        '''
        Lazy load the redis connection
        '''
        try:
            return self._redis
        except AttributeError:
            self._redis = get_redis_connection()
            return self._redis

    def get_keys(self, list_names):
        return [self.get_key(list_name) for list_name in list_names]

    def add(self, **kwargs):
        if kwargs:
            pipe = self.redis.pipeline()

            for list_name, values in six.iteritems(kwargs):
                if values:
                    key = self.get_key(list_name)
                    for value in values:
                        pipe.rpush(key, value)
                    # Removes items from list's head
                    pipe.ltrim(key, -self.max_length, -1)

            pipe.execute()

    def remove(self, **kwargs):
        if kwargs:
            pipe = self.redis.pipeline()

            for list_name, values in six.iteritems(kwargs):
                key = self.get_key(list_name)
                for value in values:
                    # Removes all occurrences of value in the list
                    pipe.lrem(key, 0, value)

            pipe.execute()

    def count(self, *args):
        if args:
            keys = self.get_keys(args)
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.llen(key)
            return self._to_result(pipe.execute())

    def get(self, *args):
        if args:
            keys = self.get_keys(args)
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.lrange(key, 0, -1)
            results = pipe.execute()
            results = [list(map(self.data_type, items)) for items in results]
            return self._to_result(results)

    def flush(self, *args):
        if args:
            keys = self.get_keys(args)
            self.redis.delete(*keys)
