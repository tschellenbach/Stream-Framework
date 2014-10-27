from stream_framework import settings
from stream_framework.feeds.base import BaseFeed
from stream_framework.storage.cassandra.activity_storage import CassandraActivityStorage
from stream_framework.storage.cassandra.timeline_storage import CassandraTimelineStorage
from stream_framework.serializers.cassandra.activity_serializer import CassandraActivitySerializer
from stream_framework.storage.cassandra import models


class CassandraFeed(BaseFeed):

    """
    Apache Cassandra feed implementation

    This implementation does not store activities in a
    denormalized fashion

    Activities are stored completely in the timeline storage

    """

    activity_storage_class = CassandraActivityStorage
    timeline_storage_class = CassandraTimelineStorage
    timeline_serializer = CassandraActivitySerializer
    timeline_model = models.Activity

    # ; the name of the column family
    timeline_cf_name = 'example'

    @classmethod
    def get_timeline_storage_options(cls):
        '''
        Returns the options for the timeline storage
        '''
        options = super(CassandraFeed, cls).get_timeline_storage_options()
        options['modelClass'] = cls.timeline_model
        options['hosts'] = settings.STREAM_CASSANDRA_HOSTS
        options['column_family_name'] = cls.timeline_cf_name
        return options

    # : clarify that this feed supports filtering and ordering
    filtering_supported = True
    ordering_supported = True
