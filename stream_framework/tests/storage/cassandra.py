import pytest
from stream_framework import settings
from stream_framework.storage.cassandra.timeline_storage import CassandraTimelineStorage
from stream_framework.tests.storage.base import TestBaseTimelineStorageClass
from stream_framework.activity import Activity
from stream_framework.storage.cassandra import models


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraTimelineStorage(TestBaseTimelineStorageClass):
    storage_cls = CassandraTimelineStorage
    storage_options = {
        'hosts': settings.STREAM_CASSANDRA_HOSTS,
        'column_family_name': 'example',
        'activity_class': Activity
    }

    def test_custom_timeline_model(self):
        CustomModel = type('custom', (models.Activity,), {})
        custom_storage_options = self.storage_options.copy()
        custom_storage_options['modelClass'] = CustomModel
        storage = self.storage_cls(**custom_storage_options)
        self.assertTrue(issubclass(storage.model, (CustomModel, )))
