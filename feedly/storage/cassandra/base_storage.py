from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.columnfamily import ColumnFamily
import logging
from pycassa.cassandra.ttypes import NotFoundException, ConsistencyLevel

logger = logging.getLogger(__name__)


column_family_cache = dict()


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family_name, **kwargs):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.column_family_name = column_family_name
        self.column_family = self.get_cached_column_family()

    def get_cached_column_family(self):
        '''
        Looks for the column family definition in the local cache
        '''
        # and now use it to look for the column family
        cf = column_family_cache.get(self.column_family_name)
        if cf is None:
            logger.info(
                'Retrieving ColumnFamily definition for %s', self.column_family_name)
            try:
                cf = ColumnFamily(
                    self.connection,
                    self.column_family_name,
                    write_consistency_level=ConsistencyLevel.ANY
                )
                column_family_cache[self.column_family_name] = cf
            except NotFoundException, e:
                cf = None

        return cf

    def get_batch_interface(self):
        return self.column_family.batch(queue_size=500)

    def flush(self):
        self.column_family.truncate()
