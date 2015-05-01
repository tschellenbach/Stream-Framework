from stream_framework.tests.storage.base_lists_storage import TestBaseListsStorage
from stream_framework.storage.redis.lists_storage import RedisListsStorage


class TestRedisListsStorage(TestBaseListsStorage):

    lists_storage_class = RedisListsStorage

    def tearDown(self):
        self.lists_storage.redis.flushall()
