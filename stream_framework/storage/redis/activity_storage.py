from stream_framework.storage.base import BaseActivityStorage
from stream_framework.storage.redis.structures.hash import ShardedHashCache
from stream_framework.serializers.activity_serializer import ActivitySerializer
import six


class ActivityCache(ShardedHashCache):
    key_format = 'activity:cache:%s'


class RedisActivityStorage(BaseActivityStorage):
    default_serializer_class = ActivitySerializer

    def get_key(self):
        return self.options.get('key', 'global')

    def get_cache(self):
        key = self.get_key()
        return ActivityCache(key)

    def get_from_storage(self, activity_ids, *args, **kwargs):
        cache = self.get_cache()
        activities = cache.get_many(activity_ids)
        activities = dict((k, six.text_type(v)) for k, v in activities.items() if v)
        return activities

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        cache = self.get_cache()
        key_value_pairs = serialized_activities.items()
        result = cache.set_many(key_value_pairs)
        insert_count = 0
        if result:
            insert_count = len(key_value_pairs)

        return insert_count

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        # we never explicitly remove things from storage
        cache = self.get_cache()
        result = cache.delete_many(activity_ids)
        return result

    def flush(self):
        cache = self.get_cache()
        cache.delete()
