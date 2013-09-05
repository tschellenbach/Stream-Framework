from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.feeds.cassandraCQL import CassandraCQLFeed
from feedly.serializers.cassandra_aggregated_activity_serializer import \
    CassandraAggregatedActivitySerializer
from feedly.storage.cassandraCQL.activity_storage import CassandraActivityStorage
from feedly.storage.cassandraCQL.timeline_storage import CassandraTimelineStorage
from feedly.storage.cassandraCQL import models


class AggregatedActivityTimelineStorage(CassandraTimelineStorage):
    base_model = models.AggregatedActivity


class CassandraAggregatedFeed(AggregatedFeed, CassandraCQLFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = AggregatedActivityTimelineStorage

    timeline_serializer = CassandraAggregatedActivitySerializer

    timeline_cf_name = 'aggregated'
