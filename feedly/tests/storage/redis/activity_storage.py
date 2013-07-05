from feedly.tests.storage.base import TestBaseActivityStorageStorage
from feedly.storage.redis.activity_storage import RedisActivityStorage


class RedisActivityStorageTest(TestBaseActivityStorageStorage):
    storage_cls = RedisActivityStorage

#
#class TestInMemoryTimelineStorageClass(TestBaseTimelineStorageClass):
#    storage_cls = InMemoryTimelineStorage
