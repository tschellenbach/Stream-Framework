from feedly.activity import Activity, AggregatedActivity


class BaseSerializer(object):

    '''
    The base serializer class, only defines the signature for
    loads and dumps

    It serializes Activity objects
    '''

    def check_type(self, data):
        if not isinstance(data, Activity):
            raise ValueError('we only know how to dump activities')

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

    def check_type(self, data):
        if not isinstance(data, AggregatedActivity):
            raise ValueError(
                'we only know how to dump AggregatedActivity not %r' % data)
