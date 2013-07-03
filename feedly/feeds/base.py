from feedly.storage.base import BaseActivityStorage
from feedly.storage.base import BaseTimelineStorage


class BaseFeed(object):

    '''
    timeline_storage one per user, contains a ordered list of activity_ids
    activity_storage keeps data related to an activity_id
    default_max_length the max length for timelines (enforced via trim method on inserts)
    serializer the class used to serialize activities (so obtain the id and the data)

    '''

    default_max_length = 100
    timeline_storage_class = BaseTimelineStorage
    activity_storage_class = BaseActivityStorage
    key_format = 'feed_%s'

    def __init__(self, user_id, timeline_storage_options, activity_storage_options):
        self.user_id = user_id
        self.timeline_storage = self.timeline_storage_class(
            **timeline_storage_options.copy())
        self.activity_storage = self.activity_storage_class(
            **activity_storage_options.copy())

    @property
    def key(self):
        return self.key_format % self.user_id

    @classmethod
    def insert_activity(cls, activity):
        cls.activity_storage_class().add(activity)

    @classmethod
    def remove_activity(cls, activity):
        cls.activity_storage_class().remove(activity)

    def add(self, activity_id, *args, **kwargs):
        return self.add_many(self.key, [activity_id], *args, **kwargs)

    def add_many(self, key, activity_ids, *args, **kwargs):
        add_count = self.timeline_storage.add_many(
            self.key, activity_ids, *args, **kwargs)
        self.timeline_storage.trim(self.key, self.max_length)
        return add_count

    def remove(self, activity, *args, **kwargs):
        return self.remove_many([activity], *args, **kwargs)

    def remove_many(self, activities, *args, **kwargs):
        return self.timeline_storage.remove_many(self.key, activities, *args, **kwargs)

    def count(self):
        return self.timeline_storage.count(self.key)

    def delete(self):
        return self.timeline_storage.delete(self.key)

    @property
    def max_length(self):
        max_length = self.default_max_length
        return max_length

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        This is the complicated stuff which allows us to slice
        """
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        # Remember if it's a slice or not. We're going to treat everything as
        # a slice to simply the logic and will `.pop()` at the end as needed.
        if isinstance(k, slice):
            start = k.start

            if k.stop is not None:
                bound = int(k.stop)
            else:
                bound = None
        else:
            start = k
            bound = k + 1

        start = start or 0

        # We need check to see if we need to populate more of the cache.
        try:
            results = self.get_results(start, bound)
        except StopIteration:
            # There's nothing left, even though the bound is higher.
            results = None

        return results

    def get_results(self, start=None, stop=None):
        '''
        Gets activity_ids from timeline_storage and then loads the
        actual data querying the activity_storage
        '''
        activity_ids = self.timeline_storage.get_many(self.key, start, stop)
        return self.activity_storage.get_many(activity_ids)
