from feedly.feed_managers.base import Feedly
from feedly.feeds.base import UserBaseFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.tests.managers.base import BaseFeedlyTest
import pytest


class CassandraUserBaseFeed(UserBaseFeed, CassandraFeed):
    pass


class CassandraFeedly(Feedly):
    feed_classes = {
        'feed': CassandraFeed
    }
    user_feed_class = CassandraUserBaseFeed


@pytest.mark.usefixtures("cassandra_reset")
class RedisFeedlyTest(BaseFeedlyTest):
    manager_class = CassandraFeedly
