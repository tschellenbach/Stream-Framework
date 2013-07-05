from pycassa.system_manager import SystemManager
from pycassa.system_manager import SIMPLE_STRATEGY
from pycassa.system_manager import UTF8_TYPE
import pytest


@pytest.fixture
def cassandra_reset():
    hostname = '192.168.50.44'
    keyspace = 'test_feedly'

    sys = SystemManager(hostname)

    # sys.drop_keyspace(keyspace)

    if keyspace not in sys.list_keyspaces():
        sys.create_keyspace(
            keyspace, SIMPLE_STRATEGY, {'replication_factor': '1'}
        )

        sys.create_column_family(
            keyspace, 'activity', comparator_type=UTF8_TYPE
        )

        sys.create_column_family(
            keyspace, 'timeline', comparator_type=UTF8_TYPE
        )
