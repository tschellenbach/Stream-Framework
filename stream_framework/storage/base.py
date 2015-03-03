from stream_framework.serializers.dummy import DummySerializer
from stream_framework.serializers.simple_timeline_serializer import \
    SimpleTimelineSerializer
from stream_framework.utils import get_metrics_instance
from stream_framework.activity import AggregatedActivity, Activity
import uuid
import six


class BaseStorage(object):

    '''
    The feed uses two storage classes, the
    - Activity Storage and the
    - Timeline Storage

    The process works as follows::

        feed = BaseFeed()
        # the activity storage is used to store the activity and mapped to an id
        feed.insert_activity(activity)
        # now the id is inserted into the timeline storage
        feed.add(activity)

    Currently there are two activity storage classes ready for production:

    - Cassandra
    - Redis

    The storage classes always receive a full activity object.
    The serializer class subsequently determines how to transform the activity
    into something the database can store.
    '''
    #: The default serializer class to use
    default_serializer_class = DummySerializer
    metrics = get_metrics_instance()

    activity_class = Activity
    aggregated_activity_class = AggregatedActivity

    def __init__(self, serializer_class=None, activity_class=None, **options):
        '''
        :param serializer_class: allows you to overwrite the serializer class
        '''
        self.serializer_class = serializer_class or self.default_serializer_class
        self.options = options
        if activity_class is not None:
            self.activity_class = activity_class
        aggregated_activity_class = options.pop(
            'aggregated_activity_class', None)
        if aggregated_activity_class is not None:
            self.aggregated_activity_class = aggregated_activity_class

    def flush(self):
        '''
        Flushes the entire storage
        '''
        pass

    def activities_to_ids(self, activities_or_ids):
        '''
        Utility function for lower levels to chose either serialize
        '''
        ids = []
        for activity_or_id in activities_or_ids:
            ids.append(self.activity_to_id(activity_or_id))
        return ids

    def activity_to_id(self, activity):
        return getattr(activity, 'serialization_id', activity)

    @property
    def serializer(self):
        '''
        Returns an instance of the serializer class

        The serializer needs to know about the activity and
        aggregated activity classes we're using
        '''
        serializer_class = self.serializer_class
        kwargs = {}
        if getattr(self, 'aggregated_activity_class', None) is not None:
            kwargs[
                'aggregated_activity_class'] = self.aggregated_activity_class
        serializer_instance = serializer_class(
            activity_class=self.activity_class, **kwargs)
        return serializer_instance

    def serialize_activity(self, activity):
        '''
        Serialize the activity and returns the serialized activity

        :returns str: the serialized activity
        '''
        serialized_activity = self.serializer.dumps(activity)
        return serialized_activity

    def serialize_activities(self, activities):
        '''
        Serializes the list of activities

        :param activities: the list of activities
        '''
        serialized_activities = {}
        for activity in activities:
            serialized_activity = self.serialize_activity(activity)
            serialized_activities[
                self.activity_to_id(activity)] = serialized_activity
        return serialized_activities

    def deserialize_activities(self, serialized_activities):
        '''
        Serializes the list of activities

        :param serialized_activities: the list of activities
        :param serialized_activities: a dictionary with activity ids and activities
        '''
        activities = []
        # handle the case where this is a dict
        if isinstance(serialized_activities, dict):
            serialized_activities = serialized_activities.values()

        if serialized_activities is not None:
            for serialized_activity in serialized_activities:
                activity = self.serializer.loads(serialized_activity)
                activities.append(activity)
        return activities


class BaseActivityStorage(BaseStorage):

    '''
    The Activity storage globally stores a key value mapping.
    This is used to store the mapping between an activity_id and the actual
    activity object.

    **Example**::

        storage = BaseActivityStorage()
        storage.add_many(activities)
        storage.get_many(activity_ids)

    The storage specific functions are located in

    - add_to_storage
    - get_from_storage
    - remove_from_storage
    '''

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        '''
        Adds the serialized activities to the storage layer

        :param serialized_activities: a dictionary with {id: serialized_activity}
        '''
        raise NotImplementedError()

    def get_from_storage(self, activity_ids, *args, **kwargs):
        '''
        Retrieves the given activities from the storage layer

        :param activity_ids: the list of activity ids
        :returns dict: a dictionary mapping activity ids to activities
        '''
        raise NotImplementedError()

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        '''
        Removes the specified activities

        :param activity_ids: the list of activity ids
        '''
        raise NotImplementedError()

    def get_many(self, activity_ids, *args, **kwargs):
        '''
        Gets many activities and deserializes them

        :param activity_ids: the list of activity ids
        '''
        self.metrics.on_feed_read(self.__class__, len(activity_ids))
        activities_data = self.get_from_storage(activity_ids, *args, **kwargs)
        return self.deserialize_activities(activities_data)

    def get(self, activity_id, *args, **kwargs):
        results = self.get_many([activity_id], *args, **kwargs)
        if not results:
            return None
        else:
            return results[0]

    def add(self, activity, *args, **kwargs):
        return self.add_many([activity], *args, **kwargs)

    def add_many(self, activities, *args, **kwargs):
        '''
        Adds many activities and serializes them before forwarding
        this to add_to_storage

        :param activities: the list of activities
        '''
        self.metrics.on_feed_write(self.__class__, len(activities))
        serialized_activities = self.serialize_activities(activities)
        return self.add_to_storage(serialized_activities, *args, **kwargs)

    def remove(self, activity, *args, **kwargs):
        return self.remove_many([activity], *args, **kwargs)

    def remove_many(self, activities, *args, **kwargs):
        '''
        Figures out the ids of the given activities and forwards
        The removal to the remove_from_storage function

        :param activities: the list of activities
        '''
        self.metrics.on_feed_remove(self.__class__, len(activities))

        if activities and isinstance(activities[0], (six.string_types, six.integer_types, uuid.UUID)):
            activity_ids = activities
        else:
            activity_ids = list(self.serialize_activities(activities).keys())
        return self.remove_from_storage(activity_ids, *args, **kwargs)


class BaseTimelineStorage(BaseStorage):

    '''
    The Timeline storage class handles the feed/timeline sorted part of storing
    a feed.

    **Example**::

        storage = BaseTimelineStorage()
        storage.add_many(key, activities)
        # get a sorted slice of the feed
        storage.get_slice(key, start, stop)
        storage.remove_many(key, activities)

    The storage specific functions are located in
    '''

    default_serializer_class = SimpleTimelineSerializer

    def add(self, key, activity, *args, **kwargs):
        return self.add_many(key, [activity], *args, **kwargs)

    def add_many(self, key, activities, *args, **kwargs):
        '''
        Adds the activities to the feed on the given key
        (The serialization is done by the serializer class)

        :param key: the key at which the feed is stored
        :param activities: the activities which to store
        '''
        self.metrics.on_feed_write(self.__class__, len(activities))
        serialized_activities = self.serialize_activities(activities)
        return self.add_to_storage(key, serialized_activities, *args, **kwargs)

    def remove(self, key, activity, *args, **kwargs):
        return self.remove_many(key, [activity], *args, **kwargs)

    def remove_many(self, key, activities, *args, **kwargs):
        '''
        Removes the activities from the feed on the given key
        (The serialization is done by the serializer class)

        :param key: the key at which the feed is stored
        :param activities: the activities which to remove
        '''
        self.metrics.on_feed_remove(self.__class__, len(activities))
        
        if activities and isinstance(activities[0], (six.string_types, six.integer_types, uuid.UUID)):
            serialized_activities = {a: a for a in activities}
        else:
            serialized_activities = self.serialize_activities(activities)
        
        return self.remove_from_storage(key, serialized_activities, *args, **kwargs)

    def get_index_of(self, key, activity_id):
        raise NotImplementedError()

    def remove_from_storage(self, key, serialized_activities):
        raise NotImplementedError()

    def index_of(self, key, activity_or_id):
        '''
        Returns activity's index within a feed or raises ValueError if not present

        :param key: the key at which the feed is stored
        :param activity_id: the activity's id to search
        '''
        activity_id = self.activities_to_ids([activity_or_id])[0]
        return self.get_index_of(key, activity_id)

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None, ordering_args=None):
        '''
        :param key: the key at which the feed is stored
        :param start: start
        :param stop: stop
        :returns list: Returns a list with tuples of key,value pairs
        '''
        raise NotImplementedError()

    def get_slice(self, key, start, stop, filter_kwargs=None, ordering_args=None):
        '''
        Returns a sorted slice from the storage

        :param key: the key at which the feed is stored
        '''
        activities_data = self.get_slice_from_storage(
            key, start, stop, filter_kwargs=filter_kwargs, ordering_args=ordering_args)
        activities = []
        if activities_data:
            serialized_activities = list(zip(*activities_data))[1]
            activities = self.deserialize_activities(serialized_activities)
        self.metrics.on_feed_read(self.__class__, len(activities))
        return activities

    def get_batch_interface(self):
        '''
        Returns a context manager which ensure all subsequent operations
        Happen via a batch interface

        An example is redis.map
        '''
        raise NotImplementedError()

    def trim(self, key, length):
        '''
        Trims the feed to the given length

        :param key: the key location
        :param length: the length to which to trim
        '''
        pass

    def count(self, key, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, key, *args, **kwargs):
        raise NotImplementedError()
