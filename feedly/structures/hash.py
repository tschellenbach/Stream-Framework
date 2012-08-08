import logging
from feedly.structures.base import RedisCache
logger = logging.getLogger(__name__)


class BaseRedisHashCache(RedisCache):
    key_format = 'redis:base_hash_cache:%s'
    pass


class RedisHashCache(BaseRedisHashCache):
    key_format = 'redis:hash_cache:%s'
    
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
        key = self.get_key()
        results = {}
        
        def _delete_many(redis, fields):
            for field in fields:
                logger.debug('removing field %s from %s', field, key)
                result = redis.hdel(key, field)
                results[field] = result
                
        #start a new map redis or go with the given one
        self._map_if_needed(_delete_many, fields)
        
        return results
    
    def get_many(self, fields):
        key = self.get_key()
        results = {}
        
        def _get_many(redis, fields):
            for field in fields:
                logger.debug('getting field %s from %s', field, key)
                result = redis.hget(key, field)
                results[field] = result
                
        #start a new map redis or go with the given one
        self._map_if_needed(_get_many, fields)
        
        return results
    
    def set(self, key, value):
        key_value_pairs = [(key, value)]
        results = self.set_many(key_value_pairs)
        result = results[0]
        return result
    
    def set_many(self, key_value_pairs):
        key = self.get_key()
        results = []
        
        def _set_many(redis, key_value_pairs):
            for field, value in key_value_pairs:
                logger.debug('writing hash(%s) field %s to %s', key, field, value)
                result = redis.hmset(key, {field: value})
                results.append(result)
                
        #start a new map redis or go with the given one
        self._map_if_needed(_set_many, key_value_pairs)
        
        return results
    

class DatabaseFallbackHashCache(RedisHashCache):
    key_format = 'redis:db_hash_cache:%s'
    
    def get_many(self, fields, database_fallback=True):
        key = self.get_key()
        results = {}
        
        def _get_many(redis, fields):
            for field in fields:
                logger.debug('getting field %s from %s', field, key)
                result = redis.hget(key, field)
                results[field] = result
                
        #start a new map redis or go with the given one
        self._map_if_needed(_get_many, fields)
        results = dict(results)
        
        #query missing results from the database and store them
        if database_fallback:
            missing_keys = [f for f in fields if not results[f]]
            database_results = self.get_many_from_database(missing_keys)
            #update our results with the data from the db and send them to redis
            results.update(database_results)
            self.set_many(database_results.items())
        
        return results
    
    def get_many_from_database(self, missing_keys):
        '''
        Return a dictionary with the serialized values for the missing keys
        '''
        raise NotImplementedError('Please implement this')
    
    
    

