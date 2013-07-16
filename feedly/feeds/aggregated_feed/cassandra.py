from feedly.storage.cassandra import CassandraActivityStorage
from feedly.storage.cassandra import CassandraTimelineStorage
from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.storage.utils.serializers.cassandra import ActivitySerializer
from feedly.storage.utils.serializers.pickle_serializer import AggregatedActivityPickleSerializer
from feedly.feeds.cassandra import CassandraFeed


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_serializer = ActivitySerializer
    activity_storage_class = CassandraActivityStorage
    timeline_serializer = AggregatedActivityPickleSerializer
    timeline_storage_class = CassandraTimelineStorage
