from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)
from feedly.storage.cassandra.connection import get_cassandra_connection
from feedly.storage.cassandra.maps import Activity
from pycassa.columnfamilymap import ColumnFamilyMap
from pycassa.columnfamily import ColumnFamily


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.map_column_family = ColumnFamilyMap(Activity, self.connection, column_family)
        self.column_family = ColumnFamily(self.connection, column_family)


class CassandraActivityStorage(BaseActivityStorage, CassandraBaseStorage):

    def get_from_storage(self, activity_ids, *args, **kwargs):
        pass

    def add_to_storage(self, activities, *args, **kwargs):
        pass

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        pass

    def flush(self):
        pass


class InMemoryTimelineStorage(BaseTimelineStorage, CassandraBaseStorage):

    def get_many(self, key, start, stop):
        pass

    def add_many(self, key, activity_ids, *args, **kwargs):
        pass

    def remove_many(self, key, activity_ids, *args, **kwargs):
        pass

    def count(self, key, *args, **kwargs):
        pass

    def delete(self, key, *args, **kwargs):
        pass

    def trim(self, key, length):
        pass
