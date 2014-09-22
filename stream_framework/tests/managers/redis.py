from stream_framework.feed_managers.base import stream_framework
from stream_framework.feeds.base import UserBaseFeed
from stream_framework.feeds.redis import RedisFeed
from stream_framework.tests.managers.base import Basestream_frameworkTest
import pytest


class RedisUserBaseFeed(UserBaseFeed, RedisFeed):
    pass


class Redisstream_framework(stream_framework):
    feed_classes = {
        'feed': RedisFeed
    }
    user_feed_class = RedisUserBaseFeed


@pytest.mark.usefixtures("redis_reset")
class Redisstream_frameworkTest(Basestream_frameworkTest):
    manager_class = Redisstream_framework
