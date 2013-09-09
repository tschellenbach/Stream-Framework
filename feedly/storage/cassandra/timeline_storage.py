from cqlengine import BatchQuery
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandra import models
from feedly.serializers.cassandra.activity_serializer import CassandraActivitySerializer
import logging


logger = logging.getLogger(__name__)


class CassandraTimelineStorage(BaseTimelineStorage):

    """
    A feed timeline implementation that uses Apache Cassandra as
    backend storage.

    CQL is used to access the data stored on cassandra via the ORM
    library cqlengine.

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

        for activity in query.order_by('-activity_id')[:limit]:
            results.append([activity.activity_id, activity])
        return results

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Adds the activities to the feed on the given key
        (The serialization is done by the serializer class)

        :param key: the key at which the feed is stored
        :param activities: the activities which to store

        To keep inserts fast we use cqlengine's batch_insert which uses
        prepared batches and ignore the passed batch_interface

        '''
        if batch_interface is not None:
            logger.info(
                '%r.add_to_storage batch_interface was ignored' % self.__class__)

        for model_instance in activities.values():
            model_instance.feed_id = str(key)
        self.model.objects.batch_insert(
            activities.values(), batch_size=self.insert_batch_size, atomic=False)

    def remove_from_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Deletes multiple activities from storage
        Unfortunately CQL 3.0 does not support the IN operator inside DELETE query's where-clause
        for that reason we are going to create 1 query per activity

        With cassandra >= 2.0 is possible to do this in one single query

        example:
            >>> self.model.objects.filter(feed_id=key, activity_id__in=[a.id for a in activities]).delete()

        '''
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
        batch = batch_interface or BatchQuery()
        last_activity = self.get_slice_from_storage(key, 0, length)[-1]
        if last_activity:
            for activity in self.model.filter(feed_id=key, activity_id__lt=last_activity[0]):
                activity.batch(batch).delete()
        if batch_interface is None:
            batch.execute()
