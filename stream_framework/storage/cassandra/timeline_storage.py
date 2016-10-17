from __future__ import division
import stream_framework.storage.cassandra.monkey_patch
from cassandra.query import SimpleStatement
from cassandra.cqlengine.connection import get_session
from cassandra.cqlengine.connection import execute
from cassandra.cqlengine.query import BatchQuery
from stream_framework.storage.base import BaseTimelineStorage
from stream_framework.storage.cassandra import models
from stream_framework.serializers.cassandra.activity_serializer import CassandraActivitySerializer
from stream_framework.utils import memoized
import logging


logger = logging.getLogger(__name__)


class Batch(BatchQuery):
    '''
    Performs a batch of insert queries using async connections
    '''

    def __init__(self, **kwargs):
        self.instances = []
        self._batch = BatchQuery()

    def batch_insert(self, model_instance):
        self.instances.append(model_instance)

    def __enter__(self):
        return self

    def add_query(self, query):
        self._batch.add_query(query)

    def add_callback(self, fn, *args, **kwargs):
        raise TypeError('not supported')

    def execute(self):
        promises = []
        session = get_session()
        for instance in self.instances:
            query = instance.__dmlquery__(instance.__class__, instance)
            query.batch(self._batch)
            query.save()

        for query in self._batch.queries:
            statement = SimpleStatement(str(query))
            params = query.get_context()
            promises.append(session.execute_async(statement, params))

        return [r.result() for r in promises]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execute()


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

    from stream_framework.storage.cassandra.connection import setup_connection
    setup_connection()

    default_serializer_class = CassandraActivitySerializer
    insert_batch_size = 100

    def __init__(self, serializer_class=None, modelClass=models.Activity, **options):
        self.column_family_name = options.pop('column_family_name')
        self.base_model = modelClass
        super(CassandraTimelineStorage, self).__init__(
            serializer_class, **options)
        self.model = self.get_model(self.base_model, self.column_family_name)

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
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
        trim_col = [c for c in self.model._columns.keys(
        ) if c not in self.model._primary_keys.keys()][0]
        parameters = (
            trim_col, self.model._get_keyspace(), self.column_family_name, key, length + 1)
        results = execute(query % parameters)
        
        # compatibility with both cassandra driver 2.7 and 3.0
        results_length = len(results.current_rows) if hasattr(results, 'current_rows') else len(results)
        if results_length < length:
            return
        trim_ts = (results[-1]['wt'] + results[-2]['wt']) // 2
        delete_query = "DELETE FROM %s.%s USING TIMESTAMP %s WHERE feed_id='%s';"
        delete_params = (
            self.model._get_keyspace(), self.column_family_name, trim_ts, key)
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
        serializer_class = self.serializer_class
        kwargs = {}
        if getattr(self, 'aggregated_activity_class', None) is not None:
            kwargs[
                'aggregated_activity_class'] = self.aggregated_activity_class
        serializer_instance = serializer_class(
            self.model, activity_class=self.activity_class, **kwargs)
        return serializer_instance

    def get_batch_interface(self):
        return Batch(batch_size=self.insert_batch_size, atomic_inserts=False)

    def contains(self, key, activity_id):
        return self.model.objects.filter(feed_id=key, activity_id=activity_id).count() > 0

    def index_of(self, key, activity_id):
        if not self.contains(key, activity_id):
            raise ValueError
        return self.model.objects.filter(feed_id=key, activity_id__gt=activity_id).count()

    def get_ordering_or_default(self, ordering_args):
        if ordering_args is None:
            ordering = ('-activity_id', )
        else:
            ordering = ordering_args
        return ordering

    def get_nth_item(self, key, index, ordering_args=None):
        ordering = self.get_ordering_or_default(ordering_args)
        return self.model.objects.filter(feed_id=key).order_by(*ordering).limit(index + 1)[index]

    def get_columns_to_read(self, query):
        columns = self.model._columns.keys()
        deferred_fields = getattr(query, '_defer_fields', [])
        setattr(query, '_defer_fields', [])
        columns = [c for c in columns if c not in deferred_fields]
        # Explicitly set feed_id as column because it is deferred in new
        # versions of the cassandra driver.
        return list(set(columns + ['feed_id']))

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None, ordering_args=None):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        results = []
        limit = 10 ** 6

        ordering = self.get_ordering_or_default(ordering_args)

        query = self.model.objects.filter(feed_id=key)
        if filter_kwargs:
            query = query.filter(**filter_kwargs)

        try:
            if start not in (0, None):
                offset_activity_id = self.get_nth_item(key, start, ordering)
                query = query.filter(
                    activity_id__lte=offset_activity_id.activity_id)
        except IndexError:
            return []

        if stop is not None:
            limit = (stop - (start or 0))

        cols = self.get_columns_to_read(query)
        for values in query.values_list(*cols).order_by(*ordering).limit(limit):
            activity = dict(zip(cols, values))
            results.append([activity['activity_id'], activity])
        return results
