from cqlengine import BatchQuery
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandraCQL import models
from feedly.serializers.cassandra.cql_serializer import CassandraActivitySerializer
from feedly.utils import chunks


class CassandraTimelineStorage(BaseTimelineStorage):
    from feedly.storage.cassandraCQL.connection import setup_connection
    setup_connection()

    default_serializer_class = CassandraActivitySerializer
    base_model = models.Activity

    def __init__(self, serializer_class=None, **options):
        self.column_family_name = options.pop('column_family_name')
        super(CassandraTimelineStorage, self).__init__(
            serializer_class, **options)
        self.model = self.get_model(self.base_model, self.column_family_name)

    @classmethod
    def get_model(cls, base_model, column_family_name):
        '''
        Creates an instance of the base model with the table_name (column family name)
        set to column family name
        :param base_model: the model to extend from
        :param column_family_name: the name of the column family
        '''
        camel_case = ''.join([s.capitalize()
                             for s in column_family_name.split('_')])
        class_name = '%sFeedModel' % camel_case
        return type(class_name, (base_model,), {'__table_name__': column_family_name})

    @property
    def serializer(self):
        '''
        Returns an instance of the serializer class
        '''
        return self.serializer_class(self.model)

    def get_batch_interface(self):
        return BatchQuery()

    def contains(self, key, activity_id):
        return self.model.objects.filter(feed_id=key, activity_id=activity_id).count()

    def index_of(self, key, activity_id):
        if not self.contains(key, activity_id):
            raise ValueError
        return len(self.model.objects.filter(feed_id=key, activity_id__gt=activity_id).values_list('feed_id'))

    def get_nth_item(self, key, index):
        return self.model.objects.filter(feed_id=key).order_by('-activity_id')[index]

    def get_slice_from_storage(self, key, start, stop):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        results = []
        limit = 10 ** 6

        query = self.model.objects.filter(feed_id=key)

        if start not in (0, None):
            offset_activity_id = self.get_nth_item(key, start)
            query = query.filter(
                activity_id__lte=offset_activity_id.activity_id)

        if stop is not None:
            limit = (stop - (start or 0))

        for activity in query.order_by('-activity_id')[:limit]:
            results.append([activity.activity_id, activity])
        return results

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Insert multiple columns using
        client.insert or batch_interface.insert
        '''
        batch = batch_interface or BatchQuery()
        activity_chunks = chunks(activities.itervalues(), 50)
        for activity_chunk in activity_chunks:
            for model_instance in activity_chunk:
                model_instance.feed_id = str(key)
                model_instance.batch(batch).save()
            if batch_interface is None:
                batch.execute()

    def remove_from_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        batch = batch_interface or BatchQuery()
        for activity_id in activities.keys():
            self.model(feed_id=key, activity_id=activity_id).batch(
                batch).delete()
        if batch_interface is None:
            batch.execute()

    def count(self, key, *args, **kwargs):
        return self.model.objects.filter(feed_id=key).count()

    def delete(self, key, *args, **kwargs):
        self.model.objects.filter(feed_id=key).delete()

    def trim(self, key, length, batch_interface=None):
        last_activity = self.get_slice_from_storage(key, 0, length)[-1]
        if last_activity:
            with BatchQuery():
                for activity in self.model.filter(feed_id=key, activity_id__lt=last_activity[0])[:1000]:
                    activity.delete()
