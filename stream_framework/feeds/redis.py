from stream_framework.feeds.base import BaseFeed
from stream_framework.storage.redis.activity_storage import RedisActivityStorage
from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage
from stream_framework.serializers.activity_serializer import ActivitySerializer


class RedisFeed(BaseFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage

    activity_serializer = ActivitySerializer

    # : allow you point to a different redis server as specified in
    # : settings.STREAM_REDIS_CONFIG
    redis_server = 'default'

    @classmethod
    def get_timeline_storage_options(cls):
        '''
        Returns the options for the timeline storage
        '''
        options = super(RedisFeed, cls).get_timeline_storage_options()
        options['redis_server'] = cls.redis_server
        return options

    # : clarify that this feed supports filtering and ordering
    filtering_supported = True
    ordering_supported = True
