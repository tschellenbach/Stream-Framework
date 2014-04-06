from feedly import settings
from feedly.feeds.base import BaseFeed
from feedly.storage.cassandra.activity_storage import CassandraActivityStorage
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage
from feedly.serializers.cassandra.activity_serializer import CassandraActivitySerializer


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

    # ; the name of the column family
    timeline_cf_name = 'example'

    @classmethod
    def get_timeline_storage_options(cls):
        '''
        Returns the options for the timeline storage
        '''
        options = super(CassandraFeed, cls).get_timeline_storage_options()
        options['hosts'] = settings.FEEDLY_CASSANDRA_HOSTS
        options['column_family_name'] = cls.timeline_cf_name
        return options

    # : clarify that this feed supports filtering and ordering
    filtering_supported = True
    ordering_supported = True
