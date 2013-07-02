from collections import defaultdict
from feedly.storage.base import (BaseTimelineStorage, BaseActivityStorage)
import threading


threadlocal = threading.local()
feed_store = threadlocal.feed_store = defaultdict(list)
activity_store = threadlocal.feed_store = defaultdict(dict)


class InMemoryActivityStorage(BaseActivityStorage):

    def get_many(self, key, activity_ids, *args, **kwargs):
        pass

    def add_many(self, key, activities, *args, **kwargs):
        insert_count = 0
        for activity_id, activity_data in activities.iteritems():
            if activity_id not in activity_store:
                insert_count += 1
            activity_store[activity_id] = activity_data
        return insert_count

    def remove_many(self, key, activity_ids, *args, **kwargs):
        pass

class InMemoryTimelineStorage(BaseTimelineStorage):

    def get_many(self, key, start, stop):
        return feed_store[key][start:stop]

    def add_many(self, key, activity_ids, *args, **kwargs):
        feed_store[key] += activity_ids
        feed_store[key] = sorted(feed_store[key], inverted=True)

    def remove_many(self, key, activity_ids, *args, **kwargs):
        for activity_id in activity_ids:
            try:
                feed_store[key].remove(activity_id)
            except ValueError: pass

    def count(self, key, *args, **kwargs):
        return len(feed_store[key])

    def delete(self, key, *args, **kwargs):
        del feed_store[key]

    def trim(self, key, length):
        feed_store[key] = feed_store[key][:length-1]