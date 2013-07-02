class BaseSerializer(object):

    '''
    BaseSerializer for implementation specs

    Implementations of this class should implement the following methods:

    loads (return an Activity instance from serialized data)
    get_serialized_activity (returns the serialized data for an Activity instance)
    get_serialized_activity_id (returns the id for an Activity instance)

    '''

    def loads(self, serialized_activity, *args, **kwargs):
        return serialized_activity

    def dumps(self, activity, *args, **kwargs):
        '''
        Returns the serialized version of activity and the
        '''
        s_id = self.get_serialized_activity_id(activity, *args, **kwargs)
        s_data = self.get_serialized_activity(activity, *args, **kwargs)
        return s_id, s_data

    def get_serialized_activity(self, activity, *args, **kwargs):
        '''
        Serialize the activity data
        '''
        return activity

    def get_serialized_activity_id(self, activity, *args, **kwargs):
        '''
        Returns the serialized activity id
        '''
        return activity.serialization_id
