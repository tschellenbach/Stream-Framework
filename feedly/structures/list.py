import logging
from feedly.structures.base import RedisCache
logger = logging.getLogger(__name__)


class BaseRedisListCache(RedisCache):
    '''
    Generic list functionality used for both the sorted set and list implementations
    
    Retrieve the sorted list/sorted set by using python slicing
    '''
    key_format = 'redis:base_list_cache:%s'
    max_length = 100
    
    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        This is the complicated stuff which allows us to slice
        """
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
                "Negative indexing is not supported."
        
        # Remember if it's a slice or not. We're going to treat everything as
        # a slice to simply the logic and will `.pop()` at the end as needed.
        if isinstance(k, slice):
            start = k.start
            
            if k.stop is not None:
                bound = int(k.stop)
            else:
                bound = None
        else:
            start = k
            bound = k + 1
        
        start = start or 0
        
        # We need check to see if we need to populate more of the cache.
        try:
            results = self.get_results(start, bound)
        except StopIteration:
            # There's nothing left, even though the bound is higher.
            results = None
            
        return results
    
    def get_results(self, start, stop):
        raise NotImplementedError('please define this function in subclasses')
    
    
class RedisListCache(BaseRedisListCache):
    key_format = 'redis:list_cache:%s'
    
    def get_results(self, start, stop):
        key = self.get_key()
        results = self.redis.lrange(key, start, stop)
        return results
    
    def append(self, value):
        values = [value]
        results = self.append_many(values)
        result = results[0]
        return result
    
    def append_many(self, values):
        key = self.get_key()
        results = []
        
        def _append_many(redis, values):
            for value in values:
                logger.debug('adding to %s with value %s', key, value)
                result = redis.rpush(key, value)
                results.append(result)
                
        #start a new map redis or go with the given one
        self._map_if_needed(_append_many, values)
        
        return results
    
    def remove(self, value):
        values = [value]
        results = self.remove_many(values)
        result = results[0]
        return result
    
    def remove_many(self, values):
        key = self.get_key()
        results = []
        
        def _remove_many(redis, values):
            for value in values:
                logger.debug('removing from %s with value %s', key, value)
                result = redis.lrem(key, value)
                results.append(result)
                
        #start a new map redis or go with the given one
        self._map_if_needed(_remove_many, values)
        
        return results
    
    def count(self):
        key = self.get_key()
        count = self.redis.llen(key)
        return count
    
    def trim(self):
        '''
        Removes the old items in the list
        '''
        #clean up everything with a rank lower than max items up to the end of the list
        removed = self.redis.ltrim(self.get_key(), self.max_items, -1)
        logger.info('cleaning up the list %s to a max of %s items' % (self.get_key(), self.max_items))
        return removed


class DatabaseFallbackRedisListCache(RedisListCache):
    '''
    pass
    '''
    key_format = 'redis:db_list_cache:%s'
    
    def get_results(self, start, stop):
        if stop is not None:
            redis_results = self.get_redis_results(start, stop - 1)
            required_items = stop - start
            enough_results = len(redis_results) == required_items
            assert len(redis_results) <= required_items, 'we should never have more than we ask for, start %s, stop %s' % (start, stop)
        else:
            # [start:] slicing does not know what's enough so
            # does not hit the db unless the cache is empty
            redis_results = self.get_redis_results(start, stop)
            enough_results = True
        if not redis_results or not enough_results:
            self.source = 'db'
            filtered = getattr(self, "_filtered", False)
            db_results = self.get_queryset_results(start, stop)
            
            if start == 0 and not redis_results and not filtered:
                logger.info('setting cache for type %s with len %s', self.get_key(), len(db_results))
                #only cache when we have no results, to prevent duplicates
                self.cache(db_results)
            elif start == 0 and redis_results and not filtered:
                logger.info('overwriting cache for type %s with len %s', self.get_key(), len(db_results))
                #clear the cache and add these values
                self.overwrite(db_results)
            results = db_results
            logger.info('retrieved %s to %s from db and not from cache with key %s' % (start, stop, self.get_key()))
        else:
            results = redis_results
            logger.info('retrieved %s to %s from cache on key %s' % (start, stop, self.get_key()))
        return results
    
    def get_query_results(self, start, stop):
        return self.get_queryset()[start:stop]
    
    def get_queryset(self):
        raise NotImplementedError('please define this function in subclasses')
    
    #note this is not the same as property(get_queryset) when subclassing
    @property
    def queryset(self):
        return self.get_queryset()
    
    def get_redis_results(self, start, stop):
        results = RedisListCache.get_results(self, start, stop)
        return results
    
    
    

