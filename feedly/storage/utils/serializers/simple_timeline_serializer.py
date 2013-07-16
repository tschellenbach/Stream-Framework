from feedly.activity import DehydratedActivity


class SimpleTimelineSerializer(object):

    def loads(self, serialized_activity, *args, **kwargs):
        return DehydratedActivity(serialization_id=serialized_activity)

    def dumps(self, activity, *args, **kwargs):
        '''
        Returns the serialized version of activity and the
        '''
        return activity.serialization_id
