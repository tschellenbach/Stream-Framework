from collections import defaultdict
from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)


timeline_store = defaultdict(list)
activity_store = defaultdict(dict)

def reverse_insort(a, x, lo=0, hi=None):
    """Insert item x in list a, and keep it reverse-sorted assuming a
    is reverse-sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if x > a[mid]: hi = mid
        else: lo = mid+1
    a.insert(lo, x)


class InMemoryActivityStorage(BaseActivityStorage):

    def get_from_storage(self, activity_ids, *args, **kwargs):
        return {_id: activity_store.get(_id) for _id in activity_ids}

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

    def index_of(self, key, activity_id):
        return timeline_store[key].index(activity_id)

    def get_many(self, key, start, stop):
        return timeline_store[key][start:stop]

    def add_many(self, key, activity_ids, *args, **kwargs):
        timeline = timeline_store[key]
        initial_count = len(timeline)
        for activity_id in activity_ids:
            if self.contains(key, activity_id):
                continue
            reverse_insort(timeline, activity_id)
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
