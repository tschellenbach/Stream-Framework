from feedly.feed_managers.base import Feedly
from feedly.serializers.activity_serializer import ActivitySerializer


class BaseFeed(object):
    serializer_class = ActivitySerializer

    def get_serializer(self):
        '''
        Returns an instance of the serialization class
        '''
        return self.serializer_class()
