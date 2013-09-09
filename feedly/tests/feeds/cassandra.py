from feedly.tests.feeds.base import TestBaseFeed
import pytest
from feedly.feeds.cassandra import CassandraFeed


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraBaseFeed(TestBaseFeed):
    feed_cls = CassandraFeed

    def test_add_insert_activity(self):
        pass

    def test_add_remove_activity(self):
        pass
