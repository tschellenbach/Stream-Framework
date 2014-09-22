from stream_framework.tests.feeds.base import TestBaseFeed
from stream_framework.feeds.memory import Feed


class InMemoryBaseFeed(TestBaseFeed):
    feed_cls = Feed
