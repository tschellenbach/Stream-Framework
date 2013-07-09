from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.memory import Feed
from feedly.feeds.aggregated_feed import AggregatedFeed


class TestBaseAggregatedFeed(TestBaseFeed):
    pass


class TestAggregatedFeed(TestBaseAggregatedFeed):
    feed_cls = AggregatedFeed
