from feedly.activity import Activity
from feedly.storage.cassandra.maps import ActivityMap
from feedly.verbs import get_verb_by_id
import pickle
from feedly.serializers.base import BaseSerializer


class CassandraActivitySerializer(BaseSerializer):

    def dumps(self, activity):
        return ActivityMap(
            key=str(activity.serialization_id),
            actor=activity.actor_id,
            time=activity.time,
            verb=activity.verb.id,
            object=activity.object_id,
            target=activity.target_id,
            extra_context=pickle.dumps(activity.extra_context)
        )

    def loads(self, serialized_activity):
        activity_kwargs = serialized_activity.__dict__.copy()
        activity_kwargs.pop('key')
        activity_kwargs['verb'] = get_verb_by_id(activity_kwargs['verb'])
        activity_kwargs['extra_context'] = pickle.loads(
            activity_kwargs['extra_context'])
        return Activity(**activity_kwargs)
