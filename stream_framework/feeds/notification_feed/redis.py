from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage
from stream_framework.feeds.notification_feed.base import NotificationFeed


class RedisNotificationFeed(NotificationFeed):

    timeline_storage_class = RedisTimelineStorage
    # TODO deifne Redis based id storages
    unseen_ids_storage_class = None
    unread_ids_storage_class = None