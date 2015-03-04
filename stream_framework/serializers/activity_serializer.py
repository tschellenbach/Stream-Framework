from stream_framework.serializers.base import BaseSerializer
from stream_framework.utils import epoch_to_datetime, datetime_to_epoch
from stream_framework.verbs import get_verb_by_id
import pickle
import six


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
        # keep the milliseconds
        activity_time = '%.6f' % datetime_to_epoch(activity.time)
        parts = [activity.actor_id, activity.verb.id,
                 activity.object_id, activity.target_id or 0]
        extra_context = activity.extra_context.copy()
        pickle_string = ''
        if extra_context:
            pickle_string = pickle.dumps(activity.extra_context)
            if six.PY3:
                pickle_string = pickle_string.decode('latin1')
        parts += [activity_time, pickle_string]
        serialized_activity = ','.join(map(str, parts))
        return serialized_activity

    def loads(self, serialized_activity):
        parts = serialized_activity.split(',', 5)
        # convert these to ids
        actor_id, verb_id, object_id, target_id = map(
            int, parts[:4])
        activity_datetime = epoch_to_datetime(float(parts[4]))
        pickle_string = parts[5]
        if not target_id:
            target_id = None
        verb = get_verb_by_id(verb_id)
        extra_context = {}
        if pickle_string:
            if six.PY3:
                pickle_string = pickle_string.encode('latin1')
            extra_context = pickle.loads(pickle_string)
        activity = self.activity_class(actor_id, verb, object_id, target_id,
                                       time=activity_datetime, extra_context=extra_context)

        return activity
