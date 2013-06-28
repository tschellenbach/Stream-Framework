from feedly.activity import Activity
from feedly.serializers.activity_serializer import ActivitySerializer
from feedly.verbs import get_verb_by_id
import pickle
from feedly import models

class LoveActivitySerializer(ActivitySerializer):
    '''
    It stores the entity_id as an id instead of a field in the extra context

    Serialization consists of 5 parts
    - actor_id
    - verb_id
    - object_id
    - target_id
    - entity_id (new)
    - extra_context (pickle)

    '''
    def dumps(self, activity):
        return models.LoveActivity(
            key=activity.serialization_id,
            actor=activity.actor_id,
            time=activity.time,
            verb=activity.verb.id,
            object=activity.object_id,
            target=activity.target_id,
            entity_id=activity.extra_context.get('entity_id'),
            extra_context=pickle.dumps(activity.extra_context)
        )

    def loads(self, serialised_activity):
        activity_kwargs = serialised_activity.__dict__.copy()
        activity_kwargs.pop('key')
        activity_kwargs.pop('entity_id')
        activity_kwargs['verb'] = get_verb_by_id(activity_kwargs['verb'])
        activity_kwargs['extra_context'] = pickle.loads(activity_kwargs['extra_context'])
        activity = Activity(**activity_kwargs)
        return activity
