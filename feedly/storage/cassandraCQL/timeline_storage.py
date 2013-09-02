from cqlengine import BatchQuery
from cqlengine import Token
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandraCQL import models
from feedly.serializers.cql_serializer import CQLSerializer


class CassandraTimelineStorage(BaseTimelineStorage):
    from feedly.storage.cassandraCQL import setup_connection
    setup_connection()

    default_serializer_class = CQLSerializer
    model = models.Activity

    def contains(self, key, activity_id):
        return self.model.objects.filter(user_id=key, activity_id=activity_id).count()

    def index_of(self, key, activity_id):
        pass

    def get_nth_item(self, key, index):
        return self.model.objects.filter(user_id=key)[index]

    def get_slice_from_storage(self, key, start, stop, pk_offset=False):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        if pk_offset:
            query = self.model.filter(activity_id=key, activity_id__token__lt=Token(pk_offset))
        else:
            query = self.model.all()
        return query[start:stop]

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Insert multiple columns using
        client.insert or batch_interface.insert
        '''
        batch = batch_interface or BatchQuery()
        for model_instance in activities.itervalues():
            model_instance.batch(batch).save()
        if batch_interface is None:
            batch.execute()

    def remove_from_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        self.model.objects.filter(activity_id__in=activities.keys())

    def count(self, key, *args, **kwargs):
        self.model.objects.filter(user_id=key).count()

    def delete(self, key, *args, **kwargs):
        self.model.objects.filter(user_id=key).delete()

    def trim(self, key, length, batch_interface=None):
        last_element = self.get_slice_from_storage(key, length)[-1]
        self.model.filter(pk__token__lte=Token(last_element.pk)).delete()
