from stream_framework.tests.storage.base import TestBaseTimelineStorageClass
from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage


class TestRedisTimelineStorageClass(TestBaseTimelineStorageClass):
    storage_cls = RedisTimelineStorage
