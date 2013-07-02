from feedly.serializers.base import BaseSerializer


class BaseActivityStorage(object):
    '''
    The storage class for activities data

    '''

    serializer = BaseSerializer

    def __init__(self, **options):
        self.options = options
        self.serializer = self.serializer()

    def add_to_storage(self, key, activities, *args, **kwargs):
        '''
        activities should be a dict with activity_id as keys and
        the serialized data as value
        '''
        raise NotImplementedError()

    def get_from_storage(self, key, activity_ids, *args, **kwargs):
        raise NotImplementedError()

    def remove_from_storage(self, key, activity_ids, *args, **kwargs):
        raise NotImplementedError()

    def get_many(self, key, activity_ids, *args, **kwargs):
        activities_data = self.get_from_storage(key, activity_ids, *args, **kwargs)
        return self.deserialize_activities(activities_data)

    def get(self, key, activity, *args, **kwargs):
        return self.get_many(key, [activity], *args, **kwargs)[0]

    def add(self, key, activity, *args, **kwargs):
        return self.add_many(key, [activity], *args, **kwargs)

    def add_many(self, key, activities, *args, **kwargs):
        serialized_activities = self.serialize_activities(activities)
        return self.add_to_storage(key, serialized_activities, *args, **kwargs)

    def remove(self, key, activity, *args, **kwargs):
        return self.remove_many(key, [activity], *args, **kwargs)

    def remove_many(self, key, activities, *args, **kwargs):
        activity_ids = self.serialize_activities(activities).keys()
        return self.remove_from_storage(key, activity_ids, *args, **kwargs)

    def flush(self):
        pass

    def serialize_activity(self, activity):
        activity_id, activity_data = self.serializer.dumps(activity)
        serialized_activity = dict(((activity_id, activity_data),))
        return serialized_activity

    def serialize_activities(self, activities):
        serialized_activities = {}
        for activity in activities:
            serialized_activities.update(self.serialize_activity(activity))
        return serialized_activities

    def deserialize_activities(self, data):
        return self.serializer.loads(data)


class BaseTimelineStorage(object):
    '''
    The storage class for the feeds

    '''

    def __init__(self, **options):
        self.options = options

    def get_many(self, key, start, stop):
        raise NotImplementedError()

    def add_many(self, key, activities, *args, **kwargs):
        raise NotImplementedError()

    def remove_many(self, key, activities, *args, **kwargs):
        raise NotImplementedError()

    def trim(self, key, length):
        raise NotImplementedError()

    def count(self, key, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, key, *args, **kwargs):
        raise NotImplementedError()
