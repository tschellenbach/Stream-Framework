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
        key_score_pairs = list(cache[start:stop])
        keys = []
        if key_score_pairs:
            keys = list(zip(*key_score_pairs)[0])
        return keys

    def add_many(self, key, activity_ids, *args, **kwargs):
        cache = self.get_cache(key)
        # in case someone gives us a generator
        activity_ids = list(activity_ids)
        # turn it into key value pairs
        value_score_pairs = zip(activity_ids, activity_ids)
        result = cache.add_many(value_score_pairs)
        return result

    def remove_many(self, key, activity_ids, *args, **kwargs):
        cache = self.get_cache(key)
        results = cache.remove_many(activity_ids)
        return results

    def count(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        return int(cache.count())

    def delete(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        cache.delete()

    def trim(self, key, length):
        return
        cache = self.get_cache(key)
        cache.trim(length)
