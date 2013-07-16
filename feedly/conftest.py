from pycassa.system_manager import SystemManager
from pycassa.system_manager import SIMPLE_STRATEGY
from pycassa.system_manager import UTF8_TYPE
from pycassa.system_manager import INT_TYPE
import pytest
import redis


@pytest.fixture(autouse=True)
def celery_eager():
    from celery import current_app
    current_app.conf.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


@pytest.fixture
def redis_reset():
    redis.Redis().flushall()


@pytest.fixture
def cassandra_reset():
    hostname = 'localhost'
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
            keyspace, 'timeline', comparator_type=INT_TYPE
        )
