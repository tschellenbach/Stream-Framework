class BaseActivityStorage(object):
    '''
    The storage class for activities data

    '''

    def __init__(self, **options):
        self.options = options

    def get_many(self, key, activity_ids, *args, **kwargs):
        raise NotImplementedError()

    def get(self, key, activity_id, *args, **kwargs):
        return self.get_many(key, [activity_id], args, kwargs)

    def add(self, key, activity_id, activity_data, *args, **kwargs):
        return self.add_many(key, {activity_id: activity_data}, args, kwargs)

    def add_many(self, key, activities, *args, **kwargs):
        raise NotImplementedError()

    def remove(self, key, activity_id, *args, **kwargs):
        return self.remove_many(key, [activity_id], args, kwargs)

    def remove_many(self, key, activity_ids, *args, **kwargs):
        raise NotImplementedError()


class BaseTimelineStorage(object):
    '''
    The storage class for the feeds

    '''

    def __init__(self, **options):
        self.options = options

    def get_many(self, key, start, stop):
        raise NotImplementedError()

    def add_many(self, key, activity_ids, *args, **kwargs):
        '''
        inserts activities in the storage 
        activities is structured as a python dictonary
        eg. {'activity_id': 'activity_data'}

        '''
        raise NotImplementedError()

    def remove_many(self, key, activity_ids, *args, **kwargs):
        raise NotImplementedError()

    def trim(self, key, length):
        raise NotImplementedError()

    def count(self, key, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, key, *args, **kwargs):
        raise NotImplementedError()
