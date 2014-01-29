from collections import defaultdict
from cqlengine import BatchQuery
from cqlengine.connection import execute
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandra import models
from feedly.serializers.cassandra.activity_serializer import CassandraActivitySerializer
from feedly.utils import memoized
import logging


logger = logging.getLogger(__name__)


class Batch(BatchQuery):

    """
    Batch class which inherits from cqlengine.BatchQuery and adds speed ups
    for inserts

    """

    def __init__(self, batch_type=None, timestamp=None,
                 batch_size=100, atomic_inserts=False):
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


@memoized
def factor_model(base_model, column_family_name):
    camel_case = ''.join([s.capitalize()
                         for s in column_family_name.split('_')])
    class_name = '%sFeedModel' % camel_case
    return type(class_name, (base_model,), {'__table_name__': column_family_name})


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
        '''
        trim using Cassandra's tombstones black magic
        retrieve the WRITETIME of the last item we want to keep
        then delete everything written after that

        this is still pretty inefficient since it needs to retrieve
        length amount of items

        WARNING: since activities created using Batch share the same timestamp
        trim can trash up to (batch_size - 1) more activities than requested

        '''
        query = "SELECT WRITETIME(%s) as wt FROM %s.%s WHERE feed_id='%s' ORDER BY activity_id DESC LIMIT %s;"
        trim_col = [c for c in self.model._columns.keys() if c not in self.model._primary_keys.keys()][0]
        parameters = (trim_col, self.model._get_keyspace(), self.column_family_name, key, length+1)
        results = execute(query % parameters)
        if len(results) < length:
            return
        trim_ts = (results[-1].wt + results[-2].wt) / 2
        delete_query = "DELETE FROM %s.%s USING TIMESTAMP %s WHERE feed_id='%s';"
        delete_params = (self.model._get_keyspace(), self.column_family_name, trim_ts, key)
        execute(delete_query % delete_params)

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
        return factor_model(base_model, column_family_name)

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
        return self.model.objects.filter(feed_id=key).order_by('-activity_id').limit(index + 1)[index]

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        results = []
        limit = 10 ** 6

        query = self.model.objects.filter(feed_id=key)
        if filter_kwargs:
            query = query.filter(**filter_kwargs)

        try:
            if start not in (0, None):
                offset_activity_id = self.get_nth_item(key, start)
                query = query.filter(
                    activity_id__lte=offset_activity_id.activity_id)
        except IndexError:
            return []

        if stop is not None:
            limit = (stop - (start or 0))

        for activity in query.order_by('-activity_id').limit(limit):
            results.append([activity.activity_id, activity])
        return results
