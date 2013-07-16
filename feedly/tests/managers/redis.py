from feedly.feed_managers.base import Feedly
from feedly.feeds.base import UserBaseFeed
from feedly.feeds.redis import RedisFeed
from feedly.tests.managers.base import BaseFeedlyTest
import pytest


class RedisUserBaseFeed(UserBaseFeed, RedisFeed):
    pass


class RedisFeedly(Feedly):
    feed_classes = {
        'feed': RedisFeed
    }
    user_feed_class = RedisUserBaseFeed


@pytest.mark.usefixtures("redis_reset")
class RedisFeedlyTest(BaseFeedlyTest):
    manager_class = RedisFeedly
