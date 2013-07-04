from feedly.storage.base import BaseActivityStorage
from feedly.storage.utils.serializers.love_activity_serializer import LoveActivitySerializer
from feedly.storage.redis.structures.hash import ShardedHashCache


class ActivityCache(ShardedHashCache):
    key_format = 'activity:cache:%s'
    

class RedisActivityStorage(BaseActivityStorage):
    serializer = LoveActivitySerializer
    
    def get_key(self):
        return self.options.get('key', 'global')
    
    def get_cache(self):
        key = self.get_key()
        return ShardedHashCache(key)

    def get_from_storage(self, activity_ids, *args, **kwargs):
        cache = self.get_cache()
        activities = cache.get_many(activity_ids)
        return activities

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        cache = self.get_cache()
        key_value_pairs = serialized_activities.items()
        insert_count = cache.set_many(key_value_pairs)
        return insert_count

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        # we never explicitly remove things from storage
        return

    def flush(self):
        cache = self.get_cache()
        cache.delete()
