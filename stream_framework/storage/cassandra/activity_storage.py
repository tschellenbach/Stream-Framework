from stream_framework.storage.base import BaseActivityStorage


class CassandraActivityStorage(BaseActivityStorage):

    def get_from_storage(self, activity_ids, *args, **kwargs):
        pass

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        pass

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        pass
