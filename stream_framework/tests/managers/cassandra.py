from stream_framework.feed_managers.base import Manager
from stream_framework.feeds.base import UserBaseFeed
from stream_framework.feeds.cassandra import CassandraFeed
from stream_framework.tests.managers.base import BaseManagerTest
import pytest


class CassandraUserBaseFeed(UserBaseFeed, CassandraFeed):
    pass


class CassandraManager(Manager):
    feed_classes = {
        'feed': CassandraFeed
    }
    user_feed_class = CassandraUserBaseFeed


@pytest.mark.usefixtures("cassandra_reset")
class RedisManagerTest(BaseManagerTest):
    manager_class = CassandraManager
