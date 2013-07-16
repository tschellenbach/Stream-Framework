from feedly.storage.utils.serializers.base import BaseSerializer
import pickle


class PickleSerializer(BaseSerializer):

    def loads(self, *args, **kwargs):
        return pickle.loads(*args, **kwargs)

    def dumps(self, *args, **kwargs):
        return pickle.dumps(*args, **kwargs)

class AggregatedActivityPickleSerializer(PickleSerializer):

    def loads(self, serialized_data):
        return pickle.loads(serialized_data)

    def dumps(self, aggregated, *args, **kwargs):
    	dehydrated_aggregated = aggregated.get_dehydrated()
        return pickle.dumps(dehydrated_aggregated)
