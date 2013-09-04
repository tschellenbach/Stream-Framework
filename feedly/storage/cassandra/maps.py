from pycassa.types import (IntegerType, DateType, UTF8Type, BytesType)


class BaseCassandraMap(object):
    pass


class ActivityMap(BaseCassandraMap):

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    key = UTF8Type()
    actor = IntegerType()
    time = DateType()
    verb = IntegerType()
    object = IntegerType()
    target = IntegerType()
    extra_context = BytesType()
