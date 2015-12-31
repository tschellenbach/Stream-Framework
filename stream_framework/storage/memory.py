from stream_framework.storage.base import (BaseTimelineStorage, BaseActivityStorage)
from collections import defaultdict
from contextlib import contextmanager
import six


timeline_store = defaultdict(list)
activity_store = defaultdict(dict)


def reverse_bisect_left(a, x, lo=0, hi=None):
    '''
    same as python bisect.bisect_left but for
    lists with reversed order
    '''
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if x > a[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


class InMemoryActivityStorage(BaseActivityStorage):

    def get_from_storage(self, activity_ids, *args, **kwargs):
        return {_id: activity_store.get(_id) for _id in activity_ids}

    def add_to_storage(self, activities, *args, **kwargs):
        insert_count = 0
        for activity_id, activity_data in six.iteritems(activities):
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

    def get_index_of(self, key, activity_id):
        return timeline_store[key].index(activity_id)

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None, ordering_args=None):
        results = list(timeline_store[key][start:stop])
        score_value_pairs = list(zip(results, results))
        return score_value_pairs

    def add_to_storage(self, key, activities, *args, **kwargs):
        timeline = timeline_store[key]
        initial_count = len(timeline)
        for activity_id, activity_data in six.iteritems(activities):
            if self.contains(key, activity_id):
                continue
            timeline.insert(reverse_bisect_left(
                timeline, activity_id), activity_data)
        return len(timeline) - initial_count

    def remove_from_storage(self, key, activities, *args, **kwargs):
        timeline = timeline_store[key]
        initial_count = len(timeline)
        for activity_id in activities.keys():
            if self.contains(key, activity_id):
                timeline.remove(activity_id)
        return initial_count - len(timeline)

    @classmethod
    def get_batch_interface(cls):
        @contextmanager
        def meandmyself():
            yield cls
        return meandmyself()

    def count(self, key, *args, **kwargs):
        return len(timeline_store[key])

    def delete(self, key, *args, **kwargs):
        timeline_store.pop(key, None)

    def trim(self, key, length):
        timeline_store[key] = timeline_store[key][:length]
