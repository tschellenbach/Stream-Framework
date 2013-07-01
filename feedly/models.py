from feedly.utils import datetime_to_epoch
from pycassa.types import (IntegerType, DateType, UTF8Type, BytesType)


# TODO: Merge serialisers and models and activity models
# TODO: Add model managers (bit smarter ColumnFamilyMap classes)

class CassandraModel(object):
    key = UTF8Type()

    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)

class LoveActivity(CassandraModel):
    '''
    TODO: change and support multiple content type
    (via verb attribute)
    features and semantyc (maybe rename it to ActivityEvent ?)
    '''
    actor = IntegerType()
    time = DateType()
    verb = IntegerType()
    object = IntegerType()
    target = IntegerType()
    entity_id = IntegerType()
    extra_context = BytesType()


class AggregatedActivity(CassandraModel):
    v3group = UTF8Type()
    created_at = DateType()
    updated_at = DateType()
    seen_at = DateType()
    read_at = DateType()
    aggregated_activities = BytesType()

    @property
    def super_column(self):
        verb_part = ''.join(
            map(str, [v.id for v in self.aggregated_activities.verbs]))
        epoch = datetime_to_epoch(self.updated_at)
        score = long(unicode(epoch) + verb_part)
        return score


class FeedEntry(CassandraModel):
    activity_id = IntegerType()
