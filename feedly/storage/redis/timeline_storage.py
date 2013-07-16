from feedly.storage.base import BaseTimelineStorage
from feedly.storage.redis.structures.sorted_set import RedisSortedSetCache
from feedly.storage.redis.connection import get_redis_connection


class TimelineCache(RedisSortedSetCache):
    sort_asc = True


class RedisTimelineStorage(BaseTimelineStorage):

    def get_cache(self, key):
        cache = TimelineCache(key)
        return cache

    def contains(self, key, activity_id):
        cache = self.get_cache(key)
        contains = cache.contains(activity_id)
        return contains

    def get_slice_from_storage(self, key, start, stop):
        cache = self.get_cache(key)
        key_score_pairs = list(cache[start:stop])
        keys = []
        if key_score_pairs:
            keys = list(zip(*key_score_pairs)[0])
        return keys

    def get_batch_interface(self):
        return get_redis_connection().map()

    def get_index_of(self, key, activity_id):
        cache = self.get_cache(key)
        index = cache.index_of(activity_id)
        return index

    def add_to_storage(self, key, activities, *args, **kwargs):
        cache = self.get_cache(key)
        # turn it into key value pairs
        value_score_pairs = zip(activities.values(), activities.keys())
        result = cache.add_many(value_score_pairs)
        for r in result:
            # errors in strings?
            # anyhow raise them here :)
            if hasattr(r, 'isdigit') and not r.isdigit():
                raise ValueError, 'got error %s in results %s' % (r, result)
        return result

    def remove_from_storage(self, key, activities, *args, **kwargs):
        cache = self.get_cache(key)
        results = cache.remove_many(activities.values())
        return results

    def count(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        return int(cache.count())

    def delete(self, key, *args, **kwargs):
        cache = self.get_cache(key)
        cache.delete()

    def trim(self, key, length):
        cache = self.get_cache(key)
        cache.trim(length)
