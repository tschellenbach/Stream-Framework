from stream_framework.tests.storage.base import TestBaseActivityStorageStorage
from stream_framework.storage.redis.activity_storage import RedisActivityStorage


class RedisActivityStorageTest(TestBaseActivityStorageStorage):
    storage_cls = RedisActivityStorage
