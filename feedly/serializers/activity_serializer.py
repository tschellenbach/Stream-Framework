from feedly.activity import Activity
from feedly.marker import FEED_END, FeedEndMarker
from feedly.serializers.base import BaseSerializer
from feedly.utils import epoch_to_datetime, datetime_to_epoch
from feedly.verbs import get_verb_by_id
import pickle


class ActivitySerializer(BaseSerializer):

    '''
    Serializer optimized for taking as little memory as possible to store an
    Activity

    It stores the entity_id as an id instead of a field in the extra context

    Serialization consists of 5 parts
    - actor_id
    - verb_id
    - object_id
    - target_id
    - entity_id (new)
    - extra_context (pickle)

    None values are stored as 0
    '''

    def dumps(self, activity):
        self.check_type(activity)
        # handle objects like the FeedEndMarker which have their own
        # serialization
        if hasattr(activity, 'serialize'):
            serialized_activity = activity.serialize()
        else:
            activity_time = datetime_to_epoch(activity.time)
            parts = [activity.actor_id, activity.verb.id,
                     activity.object_id, activity.target_id or 0]
            extra_context = activity.extra_context.copy()
            # store the entity id more efficiently
            entity_id = extra_context.pop('entity_id', 0)
            pickle_string = ''
            if extra_context:
                pickle_string = pickle.dumps(activity.extra_context)
            parts += [entity_id, activity_time, pickle_string]
            serialized_activity = ','.join(map(str, parts))
        return serialized_activity

    def loads(self, serialized_activity):
        # handle the FeedEndMarker
        if serialized_activity == FEED_END:
            activity = FeedEndMarker()
        else:
            parts = serialized_activity.split(',')
            # convert these to ids
            actor_id, verb_id, object_id, target_id, entity_id = map(
                int, parts[:5])
            activity_datetime = epoch_to_datetime(float(parts[5]))
            pickle_string = parts[6]
            if not target_id:
                target_id = None
            verb = get_verb_by_id(verb_id)
            extra_context = {}
            if pickle_string:
                extra_context = pickle.loads(pickle_string)
            if entity_id:
                extra_context['entity_id'] = entity_id
            activity = Activity(actor_id, verb, object_id, target_id,
                                time=activity_datetime, extra_context=extra_context)
        return activity
