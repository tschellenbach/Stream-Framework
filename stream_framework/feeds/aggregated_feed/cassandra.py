from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.feeds.cassandra import CassandraFeed
from stream_framework.serializers.cassandra.aggregated_activity_serializer import \
    CassandraAggregatedActivitySerializer
from stream_framework.storage.cassandra.activity_storage import CassandraActivityStorage
from stream_framework.storage.cassandra import models


class CassandraAggregatedFeed(AggregatedFeed, CassandraFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_serializer = CassandraAggregatedActivitySerializer
    timeline_cf_name = 'aggregated'
    timeline_model = models.AggregatedActivity
