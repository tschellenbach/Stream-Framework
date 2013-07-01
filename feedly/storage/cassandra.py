from pycassa.pool import ConnectionPool
from cassandra_settings import HOSTS
from cassandra_settings import KEYSPACE_NAME
from pycassa.columnfamilymap import ColumnFamilyMap
from pycassa.columnfamily import ColumnFamily
from feedly import models


connection = ConnectionPool(KEYSPACE_NAME, HOSTS)


class FeedlyColumnFamily:
    model = None
    columnfamily = None

    def __init__(self):
        self._map_store = ColumnFamilyMap(
            self.model, connection, self.columnfamily
        )
        self.store = ColumnFamily(
            connection, self.columnfamily
        )
        # copy validation from ColumnFamilyMap so we can fit
        # models as supercolumns without repeating the annoying
        # serialization/deserialization process
        # self.store.key_validation_class = self._map_store.key_validation_class
        # self.store.fields = self._map_store.fields
        # self.store.column_validators = self._map_store.column_validators
        # self.store.defaults = self._map_store.defaults

    def __getattr__(self, attrib):
        return getattr(self._map_store, attrib)

class LoveActivityStore(FeedlyColumnFamily):
    columnfamily = 'LoveActivity'
    model = models.LoveActivity

LOVE_ACTIVITY = LoveActivityStore()

class FeedStore(FeedlyColumnFamily):
    columnfamily = 'Feed'
    model = models.FeedEntry

FEED_STORE = FeedStore()

class AggregatedActivityStore(FeedlyColumnFamily):
    columnfamily = 'AggregatedFeed'
    model = models.AggregatedActivity

AGGREGATED_FEED_STORE = AggregatedActivityStore()
