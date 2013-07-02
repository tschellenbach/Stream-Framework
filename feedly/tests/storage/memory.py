from feedly.storage.memory import InMemoryActivityStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage


class MemoryActivityStorageStorage(TestBaseActivityStorageStorage):
    storage_cls = InMemoryActivityStorage
