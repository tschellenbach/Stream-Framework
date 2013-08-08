from feedly.serializers.cassandra.activity_serializer import \
    CassandraActivitySerializer
from feedly.storage.base import BaseActivityStorage
from feedly.storage.cassandra.base_storage import CassandraBaseStorage
from feedly.storage.cassandra.maps import ActivityMap
from pycassa.columnfamilymap import ColumnFamilyMap
from feedly.utils.timing import timer


class CassandraActivityStorage(CassandraBaseStorage, BaseActivityStorage):

    default_serializer_class = CassandraActivitySerializer

    def __init__(self, *args, **kwargs):
        CassandraBaseStorage.__init__(self, *args, **kwargs)
        BaseActivityStorage.__init__(self, *args, **kwargs)

    @property
    def column_family_map(self):
        if not hasattr(self, '_column_family_map'):
            setattr(self, '_column_family_map', ColumnFamilyMap(
                ActivityMap, self.connection, self.column_family_name))
        return self._column_family_map

    def get_from_storage(self, activity_ids, *args, **kwargs):
        results = self.column_family_map.multiget(keys=map(str, activity_ids))
        return results

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        self.column_family_map.batch_insert(serialized_activities.values())

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        with self.column_family.batch() as batch:
            for activity_id in activity_ids:
                batch.remove(str(activity_id))
