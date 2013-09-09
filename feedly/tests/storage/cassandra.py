from feedly import settings
from feedly.storage.cassandra.timeline_storage import CassandraTimelineStorage
from feedly.tests.storage.base import TestBaseTimelineStorageClass
import pytest


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraTimelineStorage(TestBaseTimelineStorageClass):
    storage_cls = CassandraTimelineStorage
    storage_options = {
        'hosts': settings.FEEDLY_CASSANDRA_HOSTS,
        'column_family_name': 'example'
    }
