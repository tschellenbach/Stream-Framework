from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.redis import RedisFeed


class TestRedisFeed(TestBaseFeed):
    feed_cls = RedisFeed
