from feedly.feeds.base import BaseFeed
from feedly.storage.redis.activity_storage import RedisActivityStorage
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.serializers.activity_serializer import ActivitySerializer


class RedisFeed(BaseFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage

    activity_serializer = ActivitySerializer
