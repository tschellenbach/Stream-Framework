from stream_framework.feed_managers.base import stream_framework
from stream_framework.feeds.base import UserBaseFeed
from stream_framework.feeds.cassandra import CassandraFeed
from stream_framework.tests.managers.base import Basestream_frameworkTest
import pytest


class CassandraUserBaseFeed(UserBaseFeed, CassandraFeed):
    pass


class Cassandrastream_framework(stream_framework):
    feed_classes = {
        'feed': CassandraFeed
    }
    user_feed_class = CassandraUserBaseFeed


@pytest.mark.usefixtures("cassandra_reset")
class Redisstream_frameworkTest(Basestream_frameworkTest):
    manager_class = Cassandrastream_framework
