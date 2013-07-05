from feedly.storage.base import BaseTimelineStorage
from feedly.storage.redis.structures.sorted_set import RedisSortedSetCache


class TimelineCache(RedisSortedSetCache):
    pass


class RedisTimelineStorage(BaseTimelineStorage):

    def get_cache(self, key):
        cache = TimelineCache(key)
        return cache

    def contains(self, key, activity_id):
        cache = self.get_cache(key)
        contains = cache.contains(activity_id)
        return contains

    def get_many(self, key, start, stop):
        cache = self.get_cache(key)
        return cache[start:stop]

    def add_many(self, key, activity_ids, *args, **kwargs):
        cache = self.get_cache(key)
        raise Exception, 'this cant work'

    def remove_many(self, key, activity_ids, *args, **kwargs):
        cache = self.get_cache(key)
        results = cache.remove_many(activity_ids)
        return results

    def count(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        return cache.count()

    def delete(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        cache.delete()

    def trim(self, key, length):
        cache = self.get_cache(key)
        cache.trim(length)
