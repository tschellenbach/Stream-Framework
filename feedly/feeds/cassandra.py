from feedly.feeds.base import BaseFeed
from feedly.storage.cassandra import CassandraActivityStorage
from feedly.storage.cassandra import CassandraTimelineStorage
from feedly.storage.utils.serializers.cassandra import ActivitySerializer


class Feed(BaseFeed):
    timeline_storage_class = CassandraTimelineStorage
    activity_storage_class = CassandraActivityStorage
    activity_serializer = ActivitySerializer