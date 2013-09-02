from feedly.feeds.base import BaseFeed
from feedly.storage.cassandraCQL.activity_storage import CassandraActivityStorage
from feedly.storage.cassandraCQL.timeline_storage import CassandraTimelineStorage
from feedly.serializers.cassandra.cql_serializer import CassandraActivitySerializer

class CassandraCQLFeed(BaseFeed):
    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = CassandraTimelineStorage
    timeline_serializer = CassandraActivitySerializer
