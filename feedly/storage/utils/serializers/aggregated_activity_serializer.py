from feedly.activity import AggregatedActivity
from feedly.storage.utils.serializers.love_activity_serializer import LoveActivitySerializer
from feedly import models
import pickle


class AggregatedActivitySerializer(LoveActivitySerializer):

    def __init__(self, aggregated_class=None):
        self.aggregated_class = aggregated_class or AggregatedActivity

    def dumps(self, aggregated):
        serialized = models.AggregatedActivity(
            group=aggregated.group,
            created_at=aggregated.created_at,
            updated_at=aggregated.updated_at,
            seen_at=aggregated.seen_at,
            read_at=aggregated.read_at,
            minimized_activities=aggregated.minimized_activities
        )
        # add the activities serialization
        serialized_activities = []
        for activity in aggregated.activities:
            serialized_activities.append(
                LoveActivitySerializer().dumps(activity))
        serialized.aggregated_activities = pickle.dumps(serialized_activities)
        return serialized

    def loads(self, serialized_aggregated):
        aggregated_kwargs = serialized_aggregated.__dict__.copy()
        serializations = pickle.loads(
            aggregated_kwargs.pop('aggregated_activities'))
        aggregated = self.aggregated_class(aggregated_kwargs.pop('group'))
        aggregated.__dict__.update(aggregated_kwargs)
        activities = [LoveActivitySerializer.loads(self, s)
                      for s in serializations]
        aggregated.activities = activities
        return aggregated
