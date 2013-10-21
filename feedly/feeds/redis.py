from feedly.feeds.base import BaseFeed
from feedly.storage.redis.activity_storage import RedisActivityStorage
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.serializers.activity_serializer import ActivitySerializer


class RedisFeed(BaseFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage

    activity_serializer = ActivitySerializer

    # : allow you point to a different redis server as specified in
    # : settings.FEEDLY_REDIS_CONFIG
    redis_server = 'default'

    @classmethod
    def get_timeline_storage(cls):
        timeline_storage_options = {
            'redis_server': cls.redis_server,
        }
        timeline_storage = cls.timeline_storage_class(
            **timeline_storage_options)
        return timeline_storage
