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


class CassandraActivityStorage(CassandraBaseStorage, BaseActivityStorage):
    serializer = ActivitySerializer

    def __init__(self, *args, **kwargs):
        CassandraBaseStorage.__init__(self, *args, **kwargs)
        BaseActivityStorage.__init__(self, *args, **kwargs)
        self.column_family_map = ColumnFamilyMap(ActivityMap, self.connection, self.column_family_name)

    def get_from_storage(self, activity_ids, *args, **kwargs):
        return self.column_family_map.multiget(keys=map(str, activity_ids))

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        self.column_family_map.batch_insert(serialized_activities.values())

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        with self.column_family.batch() as batch:
            for activity_id in activity_ids:
                batch.remove(str(activity_id))

    def flush(self):
        self.column_family.truncate()


class CassandraTimelineStorage(CassandraBaseStorage, BaseTimelineStorage):

    def __init__(self, *args, **kwargs):
        CassandraBaseStorage.__init__(self, *args, **kwargs)
        BaseTimelineStorage.__init__(self, *args, **kwargs)

    def get_nth_item(self, key, index):
        column_count = index
        try:
            results = self.column_family.get(key, column_count=column_count)
            if len(results) < column_count:
                return None
            item = results.keys()[-1]
            return item
        except (IndexError, NotFoundException):
            return None

    def get_many(self, key, start, stop):
        column_count = 5000
        column_start = ''

        if start not in (0, None):
            column_start = self.get_nth_item(key, start)
            if column_start is None:
                return []

        if stop is not None:
            column_count = (stop - start or 0)

        try:
            results = self.column_family.get(
                key,
                column_start=column_start,
                column_count=column_count,
                column_reversed=True
            )
        except NotFoundException:
            return []
        else:
            return results.keys()

    def add_many(self, key, activity_ids, *args, **kwargs):
        columns = { str(i): str(i) for i in activity_ids if i is not None}
        self.column_family.insert(key, columns=columns)

    def remove_many(self, key, activity_ids, *args, **kwargs):
        columns = map(str, activity_ids)
        self.column_family.remove(key, columns=columns)

    def count(self, key, *args, **kwargs):
        return self.column_family.get_count(key)

    def delete(self, key, *args, **kwargs):
        self.column_family.remove(key)

    def trim(self, key, length):
        columns = self.get_many(key, length, None)
        if columns:
            self.column_family.remove(key, columns=columns)
