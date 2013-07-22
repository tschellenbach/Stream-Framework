from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed
from feedly.feeds.aggregated_feed.notification_feed import RedisNotificationFeed


class TestNotificationFeed(TestAggregatedFeed):
    feed_cls = RedisNotificationFeed
