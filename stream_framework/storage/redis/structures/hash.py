from stream_framework.storage.redis.structures.base import RedisCache
import logging
logger = logging.getLogger(__name__)


class BaseRedisHashCache(RedisCache):
    key_format = 'redis:base_hash_cache:%s'


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
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_delete_many, fields)

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
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_set_many, key_value_pairs)

        return results


class FallbackHashCache(RedisHashCache):

    '''
    Redis structure with fallback to the database
    '''
    key_format = 'redis:db_hash_cache:%s'

    def get_many(self, fields, database_fallback=True):
        results = {}

        def _get_many(redis, fields):
            for field in fields:
                # allow for easy sharding
                key = self.get_key(field)
                logger.debug('getting field %s from %s', field, key)
                result = redis.hget(key, field)
                results[field] = result
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_get_many, fields)
        results = dict(zip(fields, results))

        # query missing results from the database and store them
        if database_fallback:
            missing_keys = [f for f in fields if not results[f]]
            database_results = self.get_many_from_fallback(missing_keys)
            # update our results with the data from the db and send them to
            # redis
            results.update(database_results)
            self.set_many(database_results.items())

        return results

    def get_many_from_fallback(self, missing_keys):
        '''
        Return a dictionary with the serialized values for the missing keys
        '''
        raise NotImplementedError('Please implement this')


class ShardedHashCache(RedisHashCache):

    '''
    Use multiple keys instead of one so its easier to shard across redis machines
    '''
    number_of_keys = 10

    def get_keys(self):
        '''
        Returns all possible keys
        '''
        keys = []
        for x in range(self.number_of_keys):
            key = self.key + ':%s' % x
            keys.append(key)
        return keys

    def get_key(self, field):
        '''
        Takes something like
        field="3,79159750" and returns 7 as the index
        '''
        import hashlib
        # redis treats everything like strings
        field = str(field).encode('utf-8')
        number = int(hashlib.md5(field).hexdigest(), 16)
        position = number % self.number_of_keys
        return self.key + ':%s' % position

    def get_many(self, fields):
        results = {}

        def _get_many(redis, fields):
            for field in fields:
                # allow for easy sharding
                key = self.get_key(field)
                logger.debug('getting field %s from %s', field, key)
                result = redis.hget(key, field)
                results[field] = result
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_get_many, fields)
        results = dict(zip(fields, results))

        return results

    def delete_many(self, fields):
        results = {}

        def _get_many(redis, fields):
            for field in fields:
                # allow for easy sharding
                key = self.get_key(field)
                logger.debug('getting field %s from %s', field, key)
                result = redis.hdel(key, field)
                results[field] = result
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_get_many, fields)
        results = dict(zip(fields, results))
        # results = dict((k, v) for k, v in results.items() if v)

        return results

    def count(self):
        '''
        Returns the number of elements in the sorted set
        '''
        logger.warn('counting all keys is slow and should be used sparsely')
        keys = self.get_keys()
        total = 0
        for key in keys:
            redis_result = self.redis.hlen(key)
            redis_count = int(redis_result)
            total += redis_count
        return total

    def contains(self, field):
        raise NotImplementedError(
            'contains isnt implemented for ShardedHashCache')

    def delete(self):
        '''
        Delete all the base variations of the key
        '''
        logger.warn('deleting all keys is slow and should be used sparsely')
        keys = self.get_keys()

        for key in keys:
            # TODO, batch this, but since we barely do this
            # not too important
            self.redis.delete(key)

    def keys(self):
        '''
        list all the keys, very slow, don't use too often
        '''
        logger.warn('listing all keys is slow and should be used sparsely')
        keys = self.get_keys()
        fields = []
        for key in keys:
            more_fields = self.redis.hkeys(key)
            fields += more_fields
        return fields


class ShardedDatabaseFallbackHashCache(ShardedHashCache, FallbackHashCache):
    pass
