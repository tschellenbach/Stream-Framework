from stream_framework.storage.memory import InMemoryTimelineStorage
from stream_framework.storage.memory import InMemoryActivityStorage
from stream_framework.tests.storage.base import TestBaseActivityStorageStorage
from stream_framework.tests.storage.base import TestBaseTimelineStorageClass


class InMemoryActivityStorage(TestBaseActivityStorageStorage):
    storage_cls = InMemoryActivityStorage


class TestInMemoryTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = InMemoryTimelineStorage
