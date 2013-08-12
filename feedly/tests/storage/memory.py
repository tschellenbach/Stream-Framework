from feedly.storage.memory import InMemoryTimelineStorage
from feedly.storage.memory import InMemoryActivityStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage
from feedly.tests.storage.base import TestBaseTimelineStorageClass


class InMemoryActivityStorage(TestBaseActivityStorageStorage):
    storage_cls = InMemoryActivityStorage


class TestInMemoryTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = InMemoryTimelineStorage
