from stream_framework.tests.storage.base_lists_storage import TestBaseListsStorage
from stream_framework.storage.redis.lists_storage import RedisListsStorage
from stream_framework.utils.five import long_t


class TestStorage(RedisListsStorage):
    data_type = long_t


class TestRedisListsStorage(TestBaseListsStorage):

    lists_storage_class = TestStorage
