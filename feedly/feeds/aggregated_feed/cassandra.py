from feedly.storage.cassandra import CassandraActivityStorage
from feedly.storage.cassandra import CassandraTimelineStorage
from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.storage.utils.serializers.pickle_serializer import PickleSerializer


class CassandraAggregatedFeed(AggregatedFeed):
    timeline_serializer = PickleSerializer
    timeline_storage_class = CassandraTimelineStorage
    activity_storage_class = CassandraActivityStorage
