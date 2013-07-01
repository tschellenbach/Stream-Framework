from pycassa.system_manager import SystemManager
from pycassa.system_manager import SIMPLE_STRATEGY
from pycassa.system_manager import UTF8_TYPE
from pycassa.system_manager import LONG_TYPE
from storage.cassandra_settings import HOSTS
from storage.cassandra_settings import KEYSPACE_NAME


sys = SystemManager(HOSTS[0])

if KEYSPACE_NAME in sys.list_keyspaces():
    sys.drop_keyspace(KEYSPACE_NAME)

sys.create_keyspace(KEYSPACE_NAME, SIMPLE_STRATEGY, {'replication_factor': '1'})
sys.create_column_family(KEYSPACE_NAME, 'LoveActivity', comparator_type=UTF8_TYPE)
sys.create_column_family(KEYSPACE_NAME, 'Feed', comparator_type=UTF8_TYPE)
sys.create_column_family(KEYSPACE_NAME, 'AggregatedFeed', comparator_type=LONG_TYPE, super=True)
