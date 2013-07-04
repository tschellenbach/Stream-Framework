from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)
from feedly.storage.cassandra.connection import get_cassandra_connection
from feedly.storage.cassandra.maps import ActivityMap
from feedly.storage.utils.serializers.cassandra import ActivitySerializer
from pycassa import NotFoundException
from pycassa.columnfamilymap import ColumnFamilyMap
from pycassa.columnfamily import ColumnFamily


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family_name):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.column_family_name = column_family_name
        self.column_family = ColumnFamily(self.connection, column_family_name)


class CassandraActivityStorage(BaseActivityStorage, CassandraBaseStorage):
    serializer = ActivitySerializer

    def __init__(self, *args, **kwargs):
        super(self, CassandraActivityStorage).__init__(*args, **kwargs)
        self.column_family_map = ColumnFamilyMap(ActivityMap, self.connection, self.column_family_name)

    def get_from_storage(self, activity_ids, *args, **kwargs):
        return self.column_family_map.multiget(keys=activity_ids)

    def add_to_storage(self, activities, *args, **kwargs):
        with self.column_family.batch() as batch:
            for activity in activities:
                batch.insert(activity)

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        with self.column_family.batch() as batch:
            for activity_id in activity_ids:
                batch.remove(activity_id)

    def flush(self):
        self.column_family.truncate()


class CassandraTimelineStorage(BaseTimelineStorage, CassandraBaseStorage):

    def get_nth_item(self, key, index):
        column_count = index + 1
        try:
            results = self.column_family.get(key, column_count=column_count)
            item = results.keys()[-1]
            return item
        except (IndexError, NotFoundException):
            return None

    def get_many(self, key, start, stop):
        column_count = None
        column_start = ''

        if start not in (0, None):
            column_start = self.get_nth_item(start)

        if stop is not None:
            column_count = (stop - start or 0) + 1

        try:
            results = self.column_family.store.get(
                self.key,
                column_start=column_start,
                column_count=column_count
            )
        except NotFoundException:
            return []
        else:
            return results

    def add_many(self, key, activity_ids, *args, **kwargs):
        columns = dict.fromkeys(activity_ids)
        self.column_family.insert(key, columns=columns)

    def remove_many(self, key, activity_ids, *args, **kwargs):
        self.column_family.remove(key, columns=activity_ids)

    def count(self, key, *args, **kwargs):
        return self.column_family.get_count(key)

    def delete(self, key, *args, **kwargs):
        self.column_family.remove(key)

    def trim(self, key, length):
        columns = self.get_many(key, length, None)
        self.column_family.remove(key, columns=columns)
