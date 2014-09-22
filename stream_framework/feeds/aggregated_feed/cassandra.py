from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.serializers.cassandra.aggregated_activity_serializer import \
    CassandraAggregatedActivitySerializer
from feedly.storage.cassandra.activity_storage import CassandraActivityStorage
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage
from feedly.storage.cassandra import models


class AggregatedActivityTimelineStorage(CassandraTimelineStorage):
    base_model = models.AggregatedActivity


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = AggregatedActivityTimelineStorage

    timeline_serializer = CassandraAggregatedActivitySerializer

    timeline_cf_name = 'aggregated'
