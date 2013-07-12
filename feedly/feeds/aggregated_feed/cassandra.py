from feedly.storage.cassandra import CassandraActivityStorage
from feedly.storage.cassandra import CassandraTimelineStorage
from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.storage.utils.serializers.cassandra import AggregatedActivitySerializer


class CassandraAggregatedFeed(AggregatedFeed):
    timeline_serializer = AggregatedActivitySerializer
    timeline_storage_class = CassandraTimelineStorage
    activity_storage_class = CassandraActivityStorage
