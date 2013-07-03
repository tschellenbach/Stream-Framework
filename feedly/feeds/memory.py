from feedly.feeds.base import BaseFeed
from feedly.storage.memory import InMemoryActivityStorage
from feedly.storage.memory import InMemoryTimelineStorage


class Feed(BaseFeed):
    timeline_storage_class = InMemoryTimelineStorage
    activity_storage_class = InMemoryActivityStorage
