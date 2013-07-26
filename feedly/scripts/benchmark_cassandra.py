from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.system_manager import SystemManager, SIMPLE_STRATEGY
import random

import logging
from pycassa.types import IntegerType
from pycassa.columnfamily import ColumnFamily
from pycassa.cassandra.ttypes import ConsistencyLevel
from django.conf import settings
try:
    # ignore this if we already configured settings
    settings.configure()
except RuntimeError, e:
    pass


logger = logging.getLogger(__name__)


def handle():
    
    from feedly.settings import FEEDLY_CASSANDRA_HOSTS

    sys = SystemManager(FEEDLY_CASSANDRA_HOSTS[0])
    
    keyspace_name = 'benchmark_cassandra_%s' % random.randint(0, 10000)
    
    print 'setting up the new keyspace'
    sys.create_keyspace(
        keyspace_name, SIMPLE_STRATEGY, {'replication_factor': '1'}
    )
    
    print 'setting up the column family benchmark'
    sys.create_column_family(
        keyspace_name, 'benchmark', comparator_type=IntegerType(reversed=True)
    )
    logger.info('inserting random data till we drop')
    
    '''
    Try:
    - a batch interface
    - 
    '''
    connection = get_cassandra_connection(keyspace_name, FEEDLY_CASSANDRA_HOSTS)
    
    column_family = ColumnFamily(
        connection,
        'benchmark',
        write_consistency_level=ConsistencyLevel.ANY
    )
    client = column_family
    
    print 'setting up the test data'
    activity_keys = range(3000, 4000)
    activity_data = ['abadfadfjkl' * 20] * len(activity_keys)
    activities = dict(zip(activity_keys, activity_data))
    print activities
    
    for x in range(1000):
        print x
        key = 'row:%s' % x
        columns = {int(k): str(v) for k, v in activities.iteritems()}
        client.insert(key, columns)
    
    
if __name__ == '__main__':
    handle()
