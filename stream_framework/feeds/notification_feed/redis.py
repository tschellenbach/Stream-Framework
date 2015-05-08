from stream_framework.feeds.notification_feed.base import BaseNotificationFeed
from stream_framework.storage.redis.lists_storage import RedisListsStorage
from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage


class RedisNotificationFeed(BaseNotificationFeed):

    markers_storage_class = RedisListsStorage
    timeline_storage_class = RedisTimelineStorage
