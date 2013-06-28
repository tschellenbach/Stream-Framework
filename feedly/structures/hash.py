import logging
from feedly.structures.base import RedisCache
logger = logging.getLogger(__name__)


class BaseRedisHashCache(RedisCache):
    key_format = 'redis:base_hash_cache:%s'
    pass


class RedisHashCache(BaseRedisHashCache):
    key_format = 'redis:hash_cache:%s'

    def get_key(self, *args, **kwargs):
        return self.key

    def count(self):
        '''
        Returns the number of elements in the sorted set
        '''
        key = self.get_key()
        redis_result = self.redis.hlen(key)
        redis_count = int(redis_result)
        return redis_count

    def contains(self, field):
        '''
        Uses hexists to see if the given field is present
        '''
        key = self.get_key()
        result = self.redis.hexists(key, field)
        activity_found = bool(result)
        return activity_found

    def get(self, field):
        fields = [field]
        results = self.get_many(fields)
        result = results[field]
        return result

    def keys(self):
        key = self.get_key()
        keys = self.redis.hkeys(key)
        return keys

    def delete_many(self, fields):
        results = {}

        def _delete_many(redis, fields):
            for field in fields:
                key = self.get_key(field)
                logger.debug('removing field %s from %s', field, key)
                result = redis.hdel(key, field)
                results[field] = result

        # start a new map redis or go with the given one
        self._map_if_needed(_delete_many, fields)

        return results

    def get_many(self, fields):
        key = self.get_key()
        results = {}
        values = list(self.redis.hmget(key, fields))
        for field, result in zip(fields, values):
            logger.debug('getting field %s from %s', field, key)
            results[field] = result

        return results

    def set(self, key, value):
        key_value_pairs = [(key, value)]
        results = self.set_many(key_value_pairs)
        result = results[0]
        return result

    def set_many(self, key_value_pairs):
        results = []

        def _set_many(redis, key_value_pairs):
            for field, value in key_value_pairs:
                key = self.get_key(field)
                logger.debug(
                    'writing hash(%s) field %s to %s', key, field, value)
                result = redis.hmset(key, {field: value})
                results.append(result)

        # start a new map redis or go with the given one
        self._map_if_needed(_set_many, key_value_pairs)

        return results
