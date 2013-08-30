from feedly import settings
from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.cassandra.ttypes import NotFoundException
from pycassa.columnfamily import ColumnFamily
import logging

logger = logging.getLogger(__name__)


column_family_cache = dict()


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family_name, batch_queue_size=150, **kwargs):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.column_family_name = column_family_name
        self.column_family = self.get_cached_column_family()
        self.batch_queue_size = batch_queue_size

    def get_cached_column_family(self):
        '''
        Looks for the column family definition in the local cache
        '''
        # not technically needed, but lets be clear about what we're doing
        global column_family_cache
        # and now use it to look for the column family
        cf = column_family_cache.get(self.column_family_name)
        if cf is None:
            logger.info(
                'Retrieving ColumnFamily definition for %s', self.column_family_name)
            try:
                cf = ColumnFamily(
                    self.connection,
                    self.column_family_name,
                    write_consistency_level=settings.FEEDLY_CASSANDRA_WRITE_CONSISTENCY_LEVEL,
                    read_consistency_level=settings.FEEDLY_CASSANDRA_READ_CONSISTENCY_LEVEL
                )
            except NotFoundException, e:
                # TODO: is this really needed ?
                cf = None
            column_family_cache[self.column_family_name] = cf
        return cf

    def get_batch_interface(self):
        return self.column_family.batch(queue_size=self.batch_queue_size)

    def flush(self):
        self.column_family.truncate()
