from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
from feedly.serializers.cassandra.activity_serializer import \
    CassandraActivitySerializer
from feedly.storage.cassandra.activity_storage import CassandraActivityStorage
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_serializer = CassandraActivitySerializer
    activity_storage_class = CassandraActivityStorage
    timeline_serializer = AggregatedActivitySerializer
    timeline_storage_class = CassandraTimelineStorage
