from stream_framework import settings
from stream_framework.storage.cassandra.timeline_storage import CassandraTimelineStorage
from stream_framework.tests.storage.base import TestBaseTimelineStorageClass
import pytest
from stream_framework.activity import Activity


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraTimelineStorage(TestBaseTimelineStorageClass):
    storage_cls = CassandraTimelineStorage
    storage_options = {
        'hosts': settings.STREAM_CASSANDRA_HOSTS,
        'column_family_name': 'example',
        'activity_class': Activity
    }
