from stream_framework.feed_managers.base import Manager
from stream_framework.feeds.base import UserBaseFeed
from stream_framework.feeds.redis import RedisFeed
from stream_framework.tests.managers.base import BaseManagerTest
import pytest


class RedisUserBaseFeed(UserBaseFeed, RedisFeed):
    pass


class RedisManager(Manager):
    feed_classes = {
        'feed': RedisFeed
    }
    user_feed_class = RedisUserBaseFeed


@pytest.mark.usefixtures("redis_reset")
class RedisManagerTest(BaseManagerTest):
    manager_class = RedisManager
