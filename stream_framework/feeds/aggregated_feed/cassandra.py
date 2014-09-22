from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.feeds.cassandra import CassandraFeed
from stream_framework.serializers.cassandra.aggregated_activity_serializer import \
    CassandraAggregatedActivitySerializer
from stream_framework.storage.cassandra.activity_storage import CassandraActivityStorage
from stream_framework.storage.cassandra.timeline_storage import CassandraTimelineStorage
from stream_framework.storage.cassandra import models


class AggregatedActivityTimelineStorage(CassandraTimelineStorage):
    base_model = models.AggregatedActivity


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = AggregatedActivityTimelineStorage

    timeline_serializer = CassandraAggregatedActivitySerializer

    timeline_cf_name = 'aggregated'
