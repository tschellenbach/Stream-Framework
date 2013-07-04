class BaseSerializer(object):

    '''
    BaseSerializer for implementation specs

    Implementations of this class should implement the following methods:

    loads (return an Activity instance from serialized data)
    serialize_activity (returns the serialized data for an Activity instance)
    serialize_activity_id (returns the id for an Activity instance)

    '''

    def loads(self, serialized_activity, *args, **kwargs):
        return serialized_activity

    def dumps(self, activity, *args, **kwargs):
        '''
        Returns the serialized version of activity and the
        '''
        return activity

