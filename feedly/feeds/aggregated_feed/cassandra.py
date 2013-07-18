from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.serializers.activity_serializer import ActivitySerializer
from feedly.serializers.pickle_serializer import \
    AggregatedActivityPickleSerializer
from feedly.storage.cassandra import CassandraActivityStorage, \
    CassandraTimelineStorage


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_serializer = ActivitySerializer
    activity_storage_class = CassandraActivityStorage
    timeline_serializer = AggregatedActivityPickleSerializer
    timeline_storage_class = CassandraTimelineStorage
