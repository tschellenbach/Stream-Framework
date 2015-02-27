from stream_framework.verbs import get_verb_by_id
from stream_framework.serializers.base import BaseSerializer
from stream_framework.utils.five import long_t
import pickle


class CassandraActivitySerializer(BaseSerializer):

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
        # TODO: convert cqlengine model to stream_framework Activity using public API
        activity_kwargs = {k: getattr(serialized_activity, k)
                           for k in serialized_activity.__dict__['_values'].keys()}
        activity_kwargs.pop('activity_id')
        activity_kwargs.pop('feed_id')
        activity_kwargs['verb'] = get_verb_by_id(int(serialized_activity.verb))
        activity_kwargs['extra_context'] = pickle.loads(
            activity_kwargs['extra_context']
        )
        return self.activity_class(**activity_kwargs)
