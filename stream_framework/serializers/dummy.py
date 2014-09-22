from stream_framework.serializers.base import BaseSerializer, BaseAggregatedSerializer


class DummySerializer(BaseSerializer):

    '''
    The dummy serializer doesnt care about the type of your data
    '''

    def check_type(self, data):
        pass


class DummyAggregatedSerializer(BaseAggregatedSerializer):

    '''
    The dummy serializer doesnt care about the type of your data
    '''

    def check_type(self, data):
        pass
