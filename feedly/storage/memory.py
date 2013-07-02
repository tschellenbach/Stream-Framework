from collections import defaultdict
from collections import OrderedDict
from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)


timeline_store = defaultdict(OrderedDict)
activity_store = defaultdict(dict)

class InMemoryActivityStorage(BaseActivityStorage):

    def get_from_storage(self, key, activity_ids, *args, **kwargs):
        return map(activity_store.get, activity_ids)

    def add_to_storage(self, key, activities, *args, **kwargs):
        insert_count = 0
        for activity_id, activity_data in activities.iteritems():
            if activity_id not in activity_store:
                insert_count += 1
            activity_store[activity_id] = activity_data
        return insert_count

    def remove_from_storage(self, key, activity_ids, *args, **kwargs):
        removed = 0
        for activity_id in activity_ids:
            exists = activity_store.pop(activity_id, None)
            if exists: removed += 1
        return removed

    def flush(self):
        activity_store.clear()


class InMemoryTimelineStorage(BaseTimelineStorage):

    def _get_sorted_columns(self, key):
        # need to use reversed order than the Orderdict
        return list(reversed(timeline_store[key].keys()))

    def get_many(self, key, start, stop):
        return self._get_sorted_columns(key)[start:stop]

    def add_many(self, key, activity_ids, *args, **kwargs):
        initial_count = len(timeline_store[key].keys())
        timeline_store[key].update(OrderedDict.fromkeys(activity_ids))
        return len(timeline_store[key].keys()) - initial_count

    def remove_many(self, key, activity_ids, *args, **kwargs):
        initial_count = len(timeline_store[key])
        for activity_id in activity_ids:
            timeline_store[key].pop(activity_id, None)
        return initial_count - len(timeline_store[key])

    def count(self, key, *args, **kwargs):
        return len(timeline_store[key])

    def delete(self, key, *args, **kwargs):
        del timeline_store[key]

    def trim(self, key, length):
        oldest_ids = self._get_sorted_columns(key)[:length]
        for activity_id in oldest_ids:
            timeline_store[key].pop(activity_id, None)
