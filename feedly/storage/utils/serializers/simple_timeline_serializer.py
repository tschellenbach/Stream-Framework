class SimpleTimelineSerializer(object):

    def loads(self, serialized_activity, *args, **kwargs):
        return serialized_activity

    def dumps(self, activity, *args, **kwargs):
        '''
        Returns the serialized version of activity and the
        '''
        return str(activity.serialization_id)
