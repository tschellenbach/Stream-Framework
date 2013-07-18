from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.storage.redis.activity_storage import RedisActivityStorage
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.serializers.aggregated_activity_serializer import AggregatedActivitySerializer
from feedly.serializers.activity_serializer import ActivitySerializer


class RedisAggregatedFeed(AggregatedFeed):
    timeline_serializer = AggregatedActivitySerializer
    activity_serializer = ActivitySerializer
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
