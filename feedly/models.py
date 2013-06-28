from django.db import models
from pycassa.types import *
from feedly.cassandra_utils.types import DatetimeType

class Activity(object):
    '''
    Base model class for activities
    Subclasses are used by FeedlyColumnFamily
    to create mappings (mainly for DRY sake)
    '''
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)

class LoveActivity(Activity):

    key = UTF8Type()
    actor = IntegerType()
    time = DatetimeType()
    verb = IntegerType()
    object = IntegerType()
    target = IntegerType()
    entity_id = IntegerType()
    extra_context = BytesType()

class AggregatedActivity(Activity):
    v3group = UTF8Type()
    created_at = DatetimeType()
    updated_at = DatetimeType()
    seen_at = DatetimeType()
    read_at = DatetimeType()
    aggregated_activities = BytesType()
