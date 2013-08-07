from feedly.feeds.aggregated_feed.redis import RedisAggregatedFeed
from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed


class TestRedisAggregatedFeed(TestAggregatedFeed):
    feed_cls = RedisAggregatedFeed
