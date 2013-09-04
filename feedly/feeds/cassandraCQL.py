from feedly import settings
from feedly.feeds.base import BaseFeed
from feedly.storage.cassandraCQL.activity_storage import CassandraActivityStorage
from feedly.storage.cassandraCQL.timeline_storage import CassandraTimelineStorage
from feedly.serializers.cassandra.cql_serializer import CassandraActivitySerializer


class CassandraCQLFeed(BaseFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = CassandraTimelineStorage
    timeline_serializer = CassandraActivitySerializer

    # ; the name of the column family
    timeline_cf_name = 'example'

    @classmethod
    def get_timeline_storage(cls):
        timeline_storage_options = {
            'hosts': settings.FEEDLY_CASSANDRA_HOSTS,
            'column_family_name': cls.timeline_cf_name,
            'serializer_class': cls.timeline_serializer
        }
        timeline_storage = cls.timeline_storage_class(
            **timeline_storage_options)
        return timeline_storage
