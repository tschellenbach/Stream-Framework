from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.storage.redis.activity_storage import RedisActivityStorage
from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage
from stream_framework.serializers.aggregated_activity_serializer import AggregatedActivitySerializer
from stream_framework.serializers.activity_serializer import ActivitySerializer


class RedisAggregatedFeed(AggregatedFeed):
    timeline_serializer = AggregatedActivitySerializer
    activity_serializer = ActivitySerializer
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
