from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.memory import Feed


class InMemoryBaseFeed(TestBaseFeed):
    feed_cls = Feed
