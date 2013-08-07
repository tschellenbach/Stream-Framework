from feedly.tests.feeds.base import TestBaseFeed
import pytest
from feedly.feeds.cassandra import CassandraFeed


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraBaseFeed(TestBaseFeed):
    feed_cls = CassandraFeed
