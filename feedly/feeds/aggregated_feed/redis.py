from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.storage.redis.activity_storage import RedisActivityStorage
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.serializers.aggregated_activity_serializer import AggregatedActivitySerializer


class RedisAggregatedFeed(AggregatedFeed):
    timeline_serializer = AggregatedActivitySerializer
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
