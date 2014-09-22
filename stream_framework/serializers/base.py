from stream_framework.activity import Activity, AggregatedActivity


class BaseSerializer(object):

    '''
    The base serializer class, only defines the signature for
    loads and dumps

    It serializes Activity objects
    '''

    def __init__(self, activity_class, *args, **kwargs):
        self.activity_class = activity_class

    def check_type(self, data):
        if not isinstance(data, Activity):
            raise ValueError('we only know how to dump activities, not %s' % type(data))

    def loads(self, serialized_activity):
        activity = serialized_activity
        return activity

    def dumps(self, activity):
        self.check_type(activity)
        return activity


class BaseAggregatedSerializer(BaseSerializer):

    '''
    Serialized aggregated activities
    '''
    #: indicates if dumps returns dehydrated aggregated activities
    dehydrate = False

    def __init__(self, aggregated_activity_class, *args, **kwargs):
        BaseSerializer.__init__(self, *args, **kwargs)
        self.aggregated_activity_class = aggregated_activity_class

    def check_type(self, data):
        if not isinstance(data, AggregatedActivity):
            raise ValueError(
                'we only know how to dump AggregatedActivity not %r' % data)
