from feedly.tests.feeds.base import TestBaseFeed
import pytest
from feedly.feeds.cassandra import CassandraCQLFeed


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraBaseFeed(TestBaseFeed):
    feed_cls = CassandraCQLFeed

    def test_add_insert_activity(self):
        pass

    def test_add_remove_activity(self):
        pass
