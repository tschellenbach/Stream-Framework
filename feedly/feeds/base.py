from feedly.storage.base import BaseActivityStorage
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.utils.serializers.base import BaseSerializer
from feedly.storage.utils.serializers.simple_timeline_serializer import SimpleTimelineSerializer


class BaseFeed(object):

    '''
    timeline_storage one per user, contains a ordered list of activity_ids
    activity_storage keeps data related to an activity_id
    default_max_length the max length for timelines (enforced via trim method on inserts)
    serializer the class used to serialize activities (so obtain the id and the data)
    '''
    default_max_length = 100

    activity_serializer = BaseSerializer
    timeline_serializer = SimpleTimelineSerializer

    timeline_storage_class = BaseTimelineStorage
    activity_storage_class = BaseActivityStorage

    key_format = 'feed_%(user_id)s'

    def __init__(self, user_id, ):
        self.user_id = user_id
        self.key_format = self.key_format

        self.timeline_storage = self.get_timeline_storage()
        self.activity_storage = self.get_activity_storage()

    @classmethod
    def get_timeline_storage(cls):
        options = {}
        options['serializer_class'] = cls.timeline_serializer
        timeline_storage = cls.timeline_storage_class(**options)
        return timeline_storage

    @classmethod
    def get_activity_storage(cls):
        options = {}
        options['serializer_class'] = cls.activity_serializer
        activity_storage = cls.activity_storage_class(**options)
        return activity_storage

    @property
    def key(self):
        return self.key_format % {'user_id': self.user_id}

    @classmethod
    def insert_activity(cls, activity, **kwargs):
        activity_storage = cls.get_activity_storage()
        activity_storage.add(activity)

    @classmethod
    def remove_activity(cls, activity, **kwargs):
        activity_storage = cls.get_activity_storage()
        activity_storage.remove(activity)

    @classmethod
    def get_timeline_batch_interface(cls):
        timeline_storage = cls.get_timeline_storage()
        return timeline_storage.get_batch_interface()

    def add(self, activity, *args, **kwargs):
        return self.add_many([activity], *args, **kwargs)

    def add_many(self, activities, *args, **kwargs):
        add_count = self.timeline_storage.add_many(
            self.key, activities, *args, **kwargs)
        self.timeline_storage.trim(self.key, self.max_length)
        return add_count

    def remove(self, activity_id, *args, **kwargs):
        return self.remove_many([activity_id], *args, **kwargs)

    def remove_many(self, activity_ids, *args, **kwargs):
        return self.timeline_storage.remove_many(self.key, activity_ids, *args, **kwargs)

    def count(self):
        return self.timeline_storage.count(self.key)

    __len__ = count

    def delete(self):
        return self.timeline_storage.delete(self.key)

    @classmethod
    def flush(cls):
        activity_storage = cls.get_activity_storage()
        timeline_storage = cls.get_timeline_storage()
        activity_storage.flush()
        timeline_storage.flush()

    @property
    def max_length(self):
        max_length = self.default_max_length
        return max_length

    def __iter__(self):
        raise TypeError('Iteration over non sliced feeds is not supported')

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

    def index_of(self, activity_id):
        return self.timeline_storage.index_of(self.key, activity_id)

    def get_results(self, start=None, stop=None):
        '''
        Gets activity_ids from timeline_storage and then loads the
        actual data querying the activity_storage
        '''
        activity_ids = self.timeline_storage.get_slice(self.key, start, stop)
        activities = self.activity_storage.get_many(activity_ids)
        return sorted(activities, reverse=True)


class UserBaseFeed(BaseFeed):
    key_format = 'user_feed:%(user_id)s'
