from feedly.feeds.base import BaseFeed
from feedly.storage.memory import InMemoryActivityStorage
from feedly.storage.memory import InMemoryTimelineStorage


class Feed(BaseFeed):
    timeline_storage = InMemoryTimelineStorage
    activity_storage = InMemoryActivityStorage
