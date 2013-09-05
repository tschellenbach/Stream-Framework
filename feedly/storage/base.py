from feedly.serializers.dummy import DummySerializer
from feedly.serializers.simple_timeline_serializer import \
    SimpleTimelineSerializer


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

    def __init__(self, serializer_class=None, **options):
        '''
        :param serializer_class: allows you to overwrite the serializer class
        '''
        self.serializer_class = serializer_class or self.default_serializer_class
        self.options = options

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
        '''
        return self.serializer_class()

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
        activity_ids = self.serialize_activities(activities).keys()
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
        serialized_activities = self.serialize_activities(activities)
        return self.remove_from_storage(key, serialized_activities, *args, **kwargs)

    def get_index_of(self, key, activity_id):
        raise NotImplementedError()

    def remove_from_storage(self, key, serialized_activities):
        raise NotImplementedError()

    def index_of(self, key, activity_or_id):
        activity_id = self.activities_to_ids([activity_or_id])[0]
        return self.get_index_of(key, activity_id)

    def get_slice_from_storage(self, key, start, stop):
        '''
        :param key: the key at which the feed is stored
        :param start: start
        :param stop: stop
        :returns list: Returns a list with tuples of key,value pairs
        '''
        raise NotImplementedError()

    def get_slice(self, key, start, stop):
        '''
        Returns a sorted slice from the storage

        :param key: the key at which the feed is stored
        '''
        activities_data = self.get_slice_from_storage(
            key, start, stop)
        activities = []
        if activities_data:
            serialized_activities = zip(*activities_data)[1]
            activities = self.deserialize_activities(serialized_activities)
        return activities

    def get_batch_interface(self):
        '''
        Returns a context manager which ensure all subsequent operations
        Happen via a batch interface

        An example is redis.map
        or pycassa's column_family.batch(queue_size=200)
        '''
        raise NotImplementedError()

    def trim(self, key, length):
        '''
        Trims the feed to the given length

        :param key: the key location
        :param length: the length to which to trim
        '''
        raise NotImplementedError()

    def count(self, key, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, key, *args, **kwargs):
        raise NotImplementedError()
