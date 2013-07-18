from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.serializers.pickle_serializer import \
    AggregatedActivityPickleSerializer
from feedly.storage.cassandra.activity_storage import CassandraActivityStorage
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_serializer = CassandraActivityStorage
    activity_storage_class = CassandraActivityStorage
    timeline_serializer = AggregatedActivityPickleSerializer
    timeline_storage_class = CassandraTimelineStorage
