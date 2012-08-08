from feedly.serializers.pickle_serializer import PickleSerializer
from feedly.marker import FEED_END, FeedEndMarker
from feedly.verbs import get_verb_by_id
from feedly.activity import Activity
import pickle


class ActivitySerializer(PickleSerializer):
    '''
    Optimized version of the Activity serializer.
    It stores the entity_id as an id instead of a field in the extra context
    
    Serialization consists of 5 parts
    - actor_id
    - verb_id
    - object_id
    - target_id
    - extra_context (pickle)
    
    None values are stored as 0
    '''
    def dumps(self, activity):
        if hasattr(activity, 'serialize'):
            serialized_activity = activity.serialize()
        else:
            parts = [activity.actor_id, activity.verb.id, activity.object_id, activity.target_id or 0]
            pickle_string = ''
            if activity.extra_context:
                pickle_string = pickle.dumps(activity.extra_context)
            parts.append(pickle_string)
            serialized_activity = ','.join(map(str, parts))
        return serialized_activity
    
    def loads(self, serialized_activity):
        if serialized_activity == FEED_END:
            activity = FeedEndMarker()
        else:
            parts = serialized_activity.split(',')
            actor_id, verb_id, object_id, target_id = map(int, parts[:4])
            if not target_id:
                target_id = None
            pickle_string = parts[4]
            verb = get_verb_by_id(verb_id)
            extra_context = {}
            if pickle_string:
                extra_context = pickle.loads(pickle_string)
            activity = Activity(actor_id, verb, object_id, target=target_id, extra_context=extra_context)
        return activity