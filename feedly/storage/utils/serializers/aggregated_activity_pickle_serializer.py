from feedly.storage.utils.serializers.pickle_serializer import PickleSerializer


class AggregatedActivitySerializer(PickleSerializer):

    def dumps(self, aggregated):
        '''
        dehidrates the aggregated activities
        '''
        aggregated.activity_ids = [activity.serialization_id for activity in aggregated.activities]
        aggregated.activities = []
        pickled_aggregated = super(AggregatedActivitySerializer, self).dumps(aggregated)
        return pickled_aggregated

    def loads(self, serialized_aggregated):
        dehidrated_aggregated = super(AggregatedActivitySerializer, self).loads(serialized_aggregated)
        return dehidrated_aggregated

    def hydrate(self, aggregated, activities):
        aggregated.activities = activities
        return aggregated
