from feedly.tests.storage.base import TestBaseTimelineStorageClass
from feedly.storage.redis.timeline_storage import RedisTimelineStorage


class TestRedisTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = RedisTimelineStorage
