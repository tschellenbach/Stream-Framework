from collections import defaultdict
from cqlengine import BatchQuery
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandra import models
from feedly.serializers.cassandra.activity_serializer import CassandraActivitySerializer
import logging


logger = logging.getLogger(__name__)


class Batch(BatchQuery):

    """
    Batch class which inherits from cqlengine.BatchQuery and adds speed ups
    for inserts

    """

    def __init__(self, batch_type=None, timestamp=None, batch_size=100, atomic_inserts=False):
        self.batch_inserts = defaultdict(list)
        self.batch_size = batch_size
        self.atomic_inserts = False
        super(Batch, self).__init__(batch_type, timestamp)

    def batch_insert(self, model_instance):
        modeltable = model_instance.__class__.__table_name__
        self.batch_inserts[modeltable].append(model_instance)

    def execute(self):
        super(Batch, self).execute()
        for instances in self.batch_inserts.values():
            modelclass = instances[0].__class__
            modelclass.objects.batch_insert(
                instances, self.batch_size, self.atomic_inserts)
        self.batch_inserts.clear()


class CassandraTimelineStorage(BaseTimelineStorage):

    """
    A feed timeline implementation that uses Apache Cassandra 2.0 for storage.

    CQL3 is used to access the data stored on Cassandra via the ORM
    library CqlEngine.

    """

    from feedly.storage.cassandra.connection import setup_connection
    setup_connection()

    default_serializer_class = CassandraActivitySerializer
    base_model = models.Activity
    insert_batch_size = 100

    def __init__(self, serializer_class=None, **options):
        self.column_family_name = options.pop('column_family_name')
        super(CassandraTimelineStorage, self).__init__(
            serializer_class, **options)
        self.model = self.get_model(self.base_model, self.column_family_name)

    def add_to_storage(self, key, activities, batch_interface=None):
        batch = batch_interface or self.get_batch_interface()
        for model_instance in activities.values():
            model_instance.feed_id = str(key)
            batch.batch_insert(model_instance)
        if batch_interface is None:
            batch.execute()

    def remove_from_storage(self, key, activities, batch_interface=None):
        batch = batch_interface or self.get_batch_interface()
        for activity_id in activities.keys():
            self.model(feed_id=key, activity_id=activity_id).batch(
                batch).delete()
        if batch_interface is None:
            batch.execute()

    def trim(self, key, length, batch_interface=None):
        batch = batch_interface or self.get_batch_interface()
        trim_slice = self.get_slice_from_storage(key, 0, length)
        if not trim_slice:
            return
        last_activity = trim_slice[-1]
        if last_activity:
            for values in self.model.filter(feed_id=key, activity_id__lt=last_activity[0]).values_list('activity_id'):
                activity_id = values[0]
                self.model(feed_id=key, activity_id=activity_id).batch(
                    batch).delete()
        if batch_interface is None:
            batch.execute()

    def count(self, key):
        return self.model.objects.filter(feed_id=key).count()

    def delete(self, key):
        self.model.objects.filter(feed_id=key).delete()

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
        return Batch(batch_size=self.insert_batch_size, atomic_inserts=False)

    def contains(self, key, activity_id):
        return self.model.objects.filter(feed_id=key, activity_id=activity_id).count() > 0

    def index_of(self, key, activity_id):
        if not self.contains(key, activity_id):
            raise ValueError
        return len(self.model.objects.filter(feed_id=key, activity_id__gt=activity_id).values_list('feed_id'))

    def get_nth_item(self, key, index):
        return self.model.objects.filter(feed_id=key).order_by('-activity_id')[index]

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        results = []
        limit = 10 ** 6

        query = self.model.objects.filter(feed_id=key)
        if filter_kwargs:
            query = query.filter(**filter_kwargs)

        if start not in (0, None):
            offset_activity_id = self.get_nth_item(key, start)
            query = query.filter(
                activity_id__lte=offset_activity_id.activity_id)

        if stop is not None:
            limit = (stop - (start or 0))

        for activity in query.order_by('-activity_id').limit(limit):
            results.append([activity.activity_id, activity])
        return results
