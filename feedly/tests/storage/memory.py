from feedly.storage.memory import InMemoryActivityStorage
from feedly.storage.memory import InMemoryTimelineStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage
from feedly.tests.storage.base import TestBaseTimelineStorageClass


class MemoryActivityStorageStorage(TestBaseActivityStorageStorage):
    storage_cls = InMemoryActivityStorage


class TestInMemoryTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = InMemoryTimelineStorage
