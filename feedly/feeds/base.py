from feedly.storage.base import BaseActivityStorage
from feedly.storage.base import BaseTimelineStorage
from feedly.storage.utils.serializers.base import BaseSerializer
from feedly.storage.utils.serializers.simple_timeline_serializer import SimpleTimelineSerializer


class BaseFeed(object):
    '''
    The BaseFeed class
    
    **Example**::
    
        feed = BaseFeed(user_id)
        # start by adding some activities
        feed.add_many([activities])
        # you can query the result like this
        results = feed[:10]
        feed.remove_many([activities])
        count = feed.count()
        feed.delete()
        
    **Subclassing**::
        
        The feed is easy to subclass.
        Commonly you'll want to change the max_length and the key_format
        
        class MyFeed(BaseFeed):
            max_length = 1000
            key_format = 'user_feed:%(user_id)s'
            
    '''
    #: the format of the key used when storing the data
    key_format = 'feed_%(user_id)s'
    
    #: the max length after which we start trimming
    max_length = 100

    #: the activity storage class to use (Redis, Cassandra etc)
    activity_storage_class = BaseActivityStorage
    #: the timeline storage class to use (Redis, Cassandra etc)
    timeline_storage_class = BaseTimelineStorage
    
    #: the class the activity storage should use for serialization
    activity_serializer = BaseSerializer
    #: the class the timline storage should use for serialization
    timeline_serializer = SimpleTimelineSerializer

    def __init__(self, user_id):
        '''
        :param user_id: the id of the user who's feed we're working on
        '''
        self.user_id = user_id
        self.key_format = self.key_format
        self.key = self.key_format % {'user_id': self.user_id}

        self.timeline_storage = self.get_timeline_storage()
        self.activity_storage = self.get_activity_storage()

    @classmethod
    def get_timeline_storage(cls):
        '''
        Returns an instance of the timeline storage
        '''
        options = {}
        options['serializer_class'] = cls.timeline_serializer
        timeline_storage = cls.timeline_storage_class(**options)
        return timeline_storage

    @classmethod
    def get_activity_storage(cls):
        '''
        Returns an instance of the activity storage
        '''
        options = {}
        options['serializer_class'] = cls.activity_serializer
        activity_storage = cls.activity_storage_class(**options)
        return activity_storage

    @classmethod
    def insert_activity(cls, activity, **kwargs):
        '''
        Inserts an activity to the activity storage
        
        :param activity: the activity class
        '''
        activity_storage = cls.get_activity_storage()
        activity_storage.add(activity)

    @classmethod
    def remove_activity(cls, activity, **kwargs):
        '''
        Removes an activity from the activity storage
        
        :param activity: the activity class
        '''
        activity_storage = cls.get_activity_storage()
        activity_storage.remove(activity)

    @classmethod
    def get_timeline_batch_interface(cls):
        timeline_storage = cls.get_timeline_storage()
        return timeline_storage.get_batch_interface()

    def add(self, activity, *args, **kwargs):
        return self.add_many([activity], *args, **kwargs)

    def add_many(self, activities, *args, **kwargs):
        '''
        Add many activities
        
        :param activities: a list of activities
        '''
        add_count = self.timeline_storage.add_many(
            self.key, activities, *args, **kwargs)
        self.timeline_storage.trim(self.key, self.max_length)
        return add_count

    def remove(self, activity_id, *args, **kwargs):
        return self.remove_many([activity_id], *args, **kwargs)

    def remove_many(self, activity_ids, *args, **kwargs):
        '''
        Remove many activities
        
        :param activities: a list of activities
        '''
        return self.timeline_storage.remove_many(self.key, activity_ids, *args, **kwargs)

    def count(self):
        '''
        Count the number of items in the feed
        '''
        return self.timeline_storage.count(self.key)

    __len__ = count

    def delete(self):
        '''
        Delete the entire feed
        '''
        return self.timeline_storage.delete(self.key)

    @classmethod
    def flush(cls):
        #TODO why do we have this method?
        activity_storage = cls.get_activity_storage()
        timeline_storage = cls.get_timeline_storage()
        activity_storage.flush()
        timeline_storage.flush()

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
        '''
        Returns the index of the activity id
        
        :param activity_id: the activity id
        '''
        return self.timeline_storage.index_of(self.key, activity_id)

    def hydrate_results(self, results):
        activity_ids = []
        for result in results:
            activity_ids += result._activities_ids
        activity_data = {a.serialization_id: a for a in self.activity_storage.get_many(activity_ids)}
        return [result.get_hydrated(activity_data) for result in results]

    def need_hydratation(self, results):
        for result in results:
            if hasattr(result, 'dehydrated') and result.dehydrated:
                return True

    def get_results(self, start=None, stop=None):
        '''
        Gets activity_ids from timeline_storage and then loads the
        actual data querying the activity_storage
        '''
        results = self.timeline_storage.get_slice(self.key, start, stop)
        if self.need_hydratation(results):
            results = self.hydrate_results(results)
        return results


class UserBaseFeed(BaseFeed):
    '''
    Implementation of the base feed with a different
    Key format
    '''
    key_format = 'user_feed:%(user_id)s'
