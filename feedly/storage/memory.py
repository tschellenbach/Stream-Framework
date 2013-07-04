import bisect
from collections import defaultdict
from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)


timeline_store = defaultdict(list)
activity_store = defaultdict(dict)


class InMemoryActivityStorage(BaseActivityStorage):

    def get_from_storage(self, activity_ids, *args, **kwargs):
        return map(activity_store.get, activity_ids)

    def add_to_storage(self, activities, *args, **kwargs):
        insert_count = 0
        for activity_id, activity_data in activities.iteritems():
            if activity_id not in activity_store:
                insert_count += 1
            activity_store[activity_id] = activity_data
        return insert_count

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        removed = 0
        for activity_id in activity_ids:
            exists = activity_store.pop(activity_id, None)
            if exists:
                removed += 1
        return removed

    def flush(self):
        activity_store.clear()


class InMemoryTimelineStorage(BaseTimelineStorage):

    def contains(self, key, activity_id):
        return activity_id in timeline_store[key]

    def get_many(self, key, start, stop):
        return timeline_store[key][start:stop]

    def add_many(self, key, activity_ids, *args, **kwargs):
        timeline = timeline_store[key]
        initial_count = len(timeline)
        for activity_id in activity_ids:
            if self.contains(key, activity_id):
                continue
            bisect.insort_left(timeline, activity_id, lo=initial_count, hi=0)
        return len(timeline) - initial_count

    def remove_many(self, key, activity_ids, *args, **kwargs):
        timeline = timeline_store[key]
        initial_count = len(timeline)
        for activity_id in activity_ids:
            if self.contains(key, activity_id):
                timeline.remove(activity_id)
        return initial_count - len(timeline)

    def count(self, key, *args, **kwargs):
        return len(timeline_store[key])

    def delete(self, key, *args, **kwargs):
        timeline_store.pop(key, None)

    def trim(self, key, length):
        timeline_store[key] = timeline_store[key][:length]
