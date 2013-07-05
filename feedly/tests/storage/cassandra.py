from feedly.storage.cassandra import CassandraActivityStorage
from feedly.storage.cassandra import CassandraTimelineStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage
from feedly.tests.storage.base import TestBaseTimelineStorageClass
import pytest


@pytest.mark.usefixtures("cassandra_reset")
class MemoryActivityStorageStorage(TestBaseActivityStorageStorage):
    storage_cls = CassandraActivityStorage
    storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['192.168.50.44'],
        'column_family_name': 'activity'
    }


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = CassandraTimelineStorage
    storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['192.168.50.44'],
        'column_family_name': 'timeline'
    }
