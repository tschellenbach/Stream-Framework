from feedly.storage.redis.activity_storage import RedisActivityStorage
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.storage.utils.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
from feedly.feeds.aggregated_feed.base import AggregatedFeed


class RedisAggregatedFeed(AggregatedFeed):
    timeline_serializer = AggregatedActivitySerializer
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
