from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.columnfamily import ColumnFamily
from feedly.utils.local import Local

'''
This is a thread local cache which works for, threads and greenlets
'''
local = Local()


class CassandraBaseStorage(object):

    def __init__(self, keyspace_name, hosts, column_family_name, **kwargs):
        self.connection = get_cassandra_connection(keyspace_name, hosts)
        self.column_family_name = column_family_name

    @property
    def column_family(self):
        cf = getattr(local, '_column_family', None)
        if cf is None:
            cf = ColumnFamily(self.connection, self.column_family_name)
            setattr(local, '_column_family', cf)
        return cf

    def get_batch_interface(self):
        return self.column_family.batch(queue_size=500)

    def flush(self):
        self.column_family.truncate()
