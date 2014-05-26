from feedly.activity import Activity
from feedly.serializers.base import BaseSerializer
from feedly.utils import epoch_to_datetime, datetime_to_epoch
from feedly.verbs import get_verb_by_id
import pickle


class ActivitySerializer(BaseSerializer):

    '''
    Serializer optimized for taking as little memory as possible to store an
    Activity

    Serialization consists of 5 parts
    - actor_id
    - verb_id
    - object_id
    - target_id
    - extra_context (pickle)

    None values are stored as 0
    '''

    def dumps(self, activity):
        self.check_type(activity)
        activity_time = datetime_to_epoch(activity.time)
        parts = [activity.actor_id, activity.verb.id,
                 activity.object_id, activity.target_id or 0]
        extra_context = activity.extra_context.copy()
        pickle_string = ''

        # dictionaries are unsorted data structures
        # however, using pickled dictionary as a key still differs by letter sequence
        # this is a temporary solution works in our case
        import operator
        extra_context = dict(sorted(extra_context.iteritems(), key=operator.itemgetter(1)))

        if extra_context:
            pickle_string = pickle.dumps(extra_context)
        parts += [activity_time, pickle_string]
        serialized_activity = ','.join(map(str, parts))
        return serialized_activity

    def loads(self, serialized_activity):
        parts = serialized_activity.split(',')
        # convert these to ids
        actor_id, verb_id, object_id, target_id = map(
            int, parts[:4])
        activity_datetime = epoch_to_datetime(float(parts[4]))
        pickle_string = str(parts[5])
        if not target_id:
            target_id = None
        verb = get_verb_by_id(verb_id)
        extra_context = {}
        if pickle_string:
            extra_context = pickle.loads(pickle_string)
        activity = self.activity_class(actor_id, verb, object_id, target_id,
                                       time=activity_datetime, extra_context=extra_context)

        return activity
