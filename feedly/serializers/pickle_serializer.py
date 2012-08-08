from feedly.serializers.base import BaseSerializer
import pickle


class PickleSerializer(BaseSerializer):
    def loads(self, *args, **kwargs):
        return pickle.loads(*args, **kwargs)
    
    def dumps(self, *args, **kwargs):
        return pickle.dumps(*args, **kwargs)