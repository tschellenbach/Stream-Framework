from feedly.storage.utils.serializers.base import BaseSerializer
from feedly.storage.utils.serializers.simple_timeline_serializer import SimpleTimelineSerializer


class BaseActivityStorage(object):

    '''
    The storage class for activities data

    '''
    default_serializer_class = BaseSerializer

    def __init__(self, serializer_class=None, **options):
        self.serializer_class = serializer_class or self.default_serializer_class
        self.options = options

    def add_to_storage(self, serialized_activities, *args, **kwargs):
        '''
        activities should be a dict with activity_id as keys and
        the serialized data as value
        '''
        raise NotImplementedError()

    def get_from_storage(self, activity_ids, *args, **kwargs):
        '''
        returns a a dict with activity_id as key and the activity
        as it is on the storage backend as value
        '''
        raise NotImplementedError()

    def remove_from_storage(self, activity_ids, *args, **kwargs):
        raise NotImplementedError()

    def get_many(self, activity_ids, *args, **kwargs):
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
        serialized_activities = self.serialize_activities(activities)
        return self.add_to_storage(serialized_activities, *args, **kwargs)

    def remove(self, activity, *args, **kwargs):
        return self.remove_many([activity], *args, **kwargs)

    def remove_many(self, activities, *args, **kwargs):
        activity_ids = self.serialize_activities(activities).keys()
        return self.remove_from_storage(activity_ids, *args, **kwargs)

    def flush(self):
        pass

    @property
    def serializer(self):
        return self.serializer_class()

    def serialize_activity(self, activity):
        activity_id = activity.serialization_id
        activity_data = self.serializer.dumps(activity)
        serialized_activity = dict(((activity_id, activity_data),))
        return serialized_activity

    def serialize_activities(self, activities):
        serialized_activities = {}
        for activity in activities:
            serialized_activities.update(self.serialize_activity(activity))
        return serialized_activities

    def deserialize_activities(self, data):
        activities = []
        for activity_id, activity_data in data.items():
            activity = self.serializer.loads(activity_data)
            activities.append(activity)
        return activities


class BaseTimelineStorage(object):

    '''
    The storage class for the feeds
    '''

    default_serializer_class = SimpleTimelineSerializer

    def __init__(self, serializer_class=None, **options):
        self.serializer_class = serializer_class or self.default_serializer_class
        self.options = options

    def index_of(self, key, activity):
        raise NotImplementedError()

    def get_many(self, key, start, stop):
        raise NotImplementedError()

    def add(self, key, activity, batch_interface=None, *args, **kwargs):
        return self.add_many(key, [activity], batch_interface, *args, **kwargs)

    def add_many(self, key, activities, batch_interface=None, *args, **kwargs):
        raise NotImplementedError()

    def flush(self):
        pass

    def get_batch_interface(self):
        raise NotImplementedError()

    def remove(self, key, activity, *args, **kwargs):
        return self.remove_many(key, [activity], *args, **kwargs)

    def remove_many(self, key, activities, *args, **kwargs):
        raise NotImplementedError()

    def trim(self, key, length):
        raise NotImplementedError()

    def count(self, key, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, key, *args, **kwargs):
        raise NotImplementedError()

    @property
    def serializer(self):
        return self.serializer_class()

    def serialize_activity(self, activity):
        activity_data = self.serializer.dumps(activity)
        return activity_data

    def serialize_activities(self, activities):
        serialized_activities = {}
        for activity in activities:
            serialized_activities.update(self.serialize_activity(activity))
        return serialized_activities

    def deserialize_activities(self, serialized_activities):
        activities = []
        for serialized_activity in serialized_activities:
            activity = self.serializer.loads(serialized_activity)
            activities.append(activity)
        return activities
