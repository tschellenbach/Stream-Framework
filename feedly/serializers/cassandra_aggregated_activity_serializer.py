from feedly.activity import AggregatedActivity
from feedly.serializers.aggregated_activity_serializer import AggregatedActivitySerializer
import pickle


class CassandraAggregatedActivitySerializer(AggregatedActivitySerializer):

    def __init__(self, model):
        self.model = model

    def dumps(self, aggregated):
        activities = pickle.dumps(aggregated.activities)
        model_instance = self.model(
            activity_id=long(aggregated.serialization_id),
            activities=activities,
            group=aggregated.group,
            created_at=aggregated.created_at,
            updated_at=aggregated.updated_at
        )
        return model_instance

    def loads(self, serialized_aggregated):
        activities = pickle.loads(serialized_aggregated.activities)
        aggregated = AggregatedActivity(
            group=serialized_aggregated.group,
            activities=activities,
            created_at=serialized_aggregated.created_at,
            updated_at=serialized_aggregated.updated_at,
        )
        return aggregated
