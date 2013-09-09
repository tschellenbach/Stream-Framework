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
    insert_batch_size = 100

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

    def get_model_columns(self):
        return self.model._columns

    def get_parametrized_insert_cql_query(self):
        from feedly import settings
        column_names = [col.db_field_name for col in self.get_model_columns().values()]
        query_def = dict(
            keyspace=settings.FEEDLY_DEFAULT_KEYSPACE,
            column_family=self.column_family_name,
            column_def=', '.join(column_names),
            param_def=', '.join('?' * len(column_names))
        )
        return "INSERT INTO %(keyspace)s.%(column_family)s (%(column_def)s) VALUES (%(param_def)s)" % query_def

    def get_insert_parameters(self, model_instance):
        dbvalues = []
        for name in self.get_model_columns().keys():
            dbvalues.append(getattr(model_instance, name))
        return dbvalues

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Insert multiple columns using
        client.insert or batch_interface.insert
        '''

        from cqlengine.connection import connection_pool # keep it here! (its magic)
        insert_queries_count = len(activities)
        query_per_batch = min(self.insert_batch_size, insert_queries_count)

        insert_query = self.get_parametrized_insert_cql_query()
        batch_query = """
            BEGIN BATCH
            {}
            APPLY BATCH;
        """

        prepared_query = connection_pool.prepare(
            batch_query.format(insert_query * query_per_batch)
        )

        if query_per_batch % insert_queries_count:
            cleanup_prepared_query = connection_pool.prepare(
                batch_query.format(insert_query * (insert_queries_count % query_per_batch) )
            )

        results = []
        activity_chunks = chunks(activities.itervalues(), query_per_batch)
        for activity_chunk in activity_chunks:
            params = []
            for model_instance in activity_chunk:
                model_instance.feed_id = str(key)
                params += self.get_insert_parameters(model_instance)
            if len(activity_chunk) == query_per_batch:
                results.append(connection_pool.execute_async(prepared_query.bind(params)))
            else:
                results.append(connection_pool.execute_async(cleanup_prepared_query.bind(params)))

        for r in results:
            r.result()

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
