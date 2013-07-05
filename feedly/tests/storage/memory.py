from feedly.storage.memory import InMemoryTimelineStorage
from feedly.tests.storage.base import TestBaseActivityStorageStorage
from feedly.tests.storage.base import TestBaseTimelineStorageClass
from feedly.storage.redis.activity_storage import RedisActivityStorage


class MemoryRedisActivityStorage(TestBaseActivityStorageStorage):
    storage_cls = RedisActivityStorage


class TestInMemoryTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = InMemoryTimelineStorage
