from feedly.storage.base import BaseTimelineStorage
from feedly.storage.redis.structures.sorted_set import RedisSortedSetCache
from feedly.storage.utils.serializers.love_activity_serializer import LoveActivitySerializer
from feedly.storage.utils.serializers.aggregated_activity_serializer import AggregatedActivitySerializer
from feedly.activity import BaseActivity


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
            keys = self.deserialize_activities(keys)
            
        return keys

    def add_many(self, key, activity_ids, *args, **kwargs):
        '''
        Activity ids is either
        - a list of activity ids to store
        - a list of activities (or aggregated activities)
        '''
        cache = self.get_cache(key)
        # in case someone gives us a generator
        activity_ids = list(activity_ids)
        # turn it into key value pairs
        if isinstance(activity_ids[0], BaseActivity):
            value_score_pairs = [(self.serialize_activity(a), a.serialization_id) for a in activity_ids]
        else:
            value_score_pairs = zip(activity_ids, activity_ids)
            
        result = cache.add_many(value_score_pairs)
        for r in result:
            # errors in strings?
            # anyhow raise them here :)
            if hasattr(r, 'isdigit') and not r.isdigit():
                raise ValueError, 'got error %s in results %s' % (r, result)
        return result

    def remove_many(self, key, activity_ids, *args, **kwargs):
        cache = self.get_cache(key)
        if isinstance(activity_ids[0], BaseActivity):
            values = [self.serialize_activity(a) for a in activity_ids]
        else:
            values = activity_ids
        
        results = cache.remove_many(values)
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
        

