from stream_framework.feeds.base import BaseFeed
from stream_framework.storage.memory import InMemoryActivityStorage
from stream_framework.storage.memory import InMemoryTimelineStorage


class Feed(BaseFeed):
    timeline_storage_class = InMemoryTimelineStorage
    activity_storage_class = InMemoryActivityStorage
