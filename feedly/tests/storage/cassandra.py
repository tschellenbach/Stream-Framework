from feedly import settings
from feedly.storage.cassandra.activity_storage import CassandraActivityStorage
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage, \
    TestBaseTimelineStorageClass
import pytest
import unittest


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraActivityStorage(TestBaseActivityStorageStorage):
    storage_cls = CassandraActivityStorage
    storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': settings.FEEDLY_CASSANDRA_HOSTS,
        'column_family_name': 'activity'
    }

    @unittest.skip('unsupported feature test')
    def test_add(self):
        pass

    @unittest.skip('unsupported feature test')
    def test_add_twice(self):
        pass


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraTimelineStorage(TestBaseTimelineStorageClass):
    storage_cls = CassandraTimelineStorage
    storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': settings.FEEDLY_CASSANDRA_HOSTS,
        'column_family_name': 'timeline'
    }
