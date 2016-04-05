from stream_framework.verbs import get_verb_by_id
from stream_framework.serializers.base import BaseSerializer
from stream_framework.utils.five import long_t
import pickle


class CassandraActivitySerializer(BaseSerializer):
    '''
    Cassandra serializer for activities. Note: unlike other serializers this serializer
    does not have symmetrical `dumps` and `loads` functions (eg. loads reads a dictionary
    and dumps returns a CQLEngine model instance)
    '''

    def __init__(self, model, *args, **kwargs):
        BaseSerializer.__init__(self, *args, **kwargs)
        self.model = model

    def dumps(self, activity):
        self.check_type(activity)
        return self.model(
            activity_id=long_t(activity.serialization_id),
            actor=activity.actor_id,
            time=activity.time,
            verb=activity.verb.id,
            object=activity.object_id,
            target=activity.target_id,
            extra_context=pickle.dumps(activity.extra_context)
        )

    def loads(self, serialized_activity):
        serialized_activity.pop('activity_id')
        serialized_activity.pop('feed_id')
        serialized_activity['verb'] = get_verb_by_id(int(serialized_activity['verb']))
        serialized_activity['extra_context'] = pickle.loads(
            serialized_activity['extra_context']
        )
        return self.activity_class(**serialized_activity)
