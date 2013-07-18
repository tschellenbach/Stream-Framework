from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.columnfamily import ColumnFamily


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family_name, **kwargs):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.column_family_name = column_family_name

    @property
    def column_family(self):
        if not hasattr(self, '_column_family'):
            setattr(self, '_column_family', ColumnFamily(self.connection, self.column_family_name))
        return self._column_family

    def get_batch_interface(self):
        return self.column_family.batch(queue_size=200)

    def flush(self):
        self.column_family.truncate()