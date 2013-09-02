from cqlengine import BatchQuery
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandraCQL import models
from feedly.serializers.cassandra.cql_serializer import CassandraActivitySerializer


class CassandraTimelineStorage(BaseTimelineStorage):
    from feedly.storage.cassandraCQL.connection import setup_connection
    setup_connection()

    default_serializer_class = CassandraActivitySerializer
    model = models.Activity

    def contains(self, key, activity_id):
        return self.model.objects.filter(user_id=key, activity_id=activity_id).count()

    def index_of(self, key, activity_id):
        if not self.contains(key, activity_id):
            raise ValueError
        return len(self.model.objects.filter(user_id=key, activity_id__gt=activity_id).values_list('user_id'))

    def get_nth_item(self, key, index):
        return self.model.objects.filter(user_id=key).order_by('-activity_id')[index]

    def get_slice_from_storage(self, key, start, stop, pk_offset=False):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        results = []
        query = self.model.filter(user_id=key)
        if pk_offset:
            query = query.filter(activity_id__lt=pk_offset)
        for activity in query.order_by('-activity_id')[start:stop]:
            results.append([activity.activity_id, activity])
        return results

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Insert multiple columns using
        client.insert or batch_interface.insert
        '''
        batch = batch_interface or BatchQuery()
        for model_instance in activities.itervalues():
            model_instance.user_id = str(key)
            model_instance.batch(batch).save()
        if batch_interface is None:
            batch.execute()

    def remove_from_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        self.model.objects.filter(activity_id__in=activities.keys())

    def count(self, key, *args, **kwargs):
        return self.model.objects.filter(user_id=key).count()

    def delete(self, key, *args, **kwargs):
        self.model.objects.filter(user_id=key).delete()

    def trim(self, key, length, batch_interface=None):
        last_activity = self.get_slice_from_storage(key, 0, length)[-1]
        if last_activity:
            with BatchQuery():
                for activity in self.model.filter(user_id=key, activity_id__lt=last_activity[0])[:1000]:
                    activity.delete()
