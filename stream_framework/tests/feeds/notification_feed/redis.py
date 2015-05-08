from stream_framework.feeds.notification_feed.redis import RedisNotificationFeed
from stream_framework.tests.feeds.notification_feed.base import TestBaseNotificationFeed


class TestRedisNotificationFeed(TestBaseNotificationFeed):
    feed_cls = RedisNotificationFeed
