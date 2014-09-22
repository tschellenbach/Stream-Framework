from stream_framework.activity import Activity, AggregatedActivity


class FakeActivity(Activity):
    pass


class FakeAggregatedActivity(AggregatedActivity):
    pass


class Pin(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
