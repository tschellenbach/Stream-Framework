from feedly.tests.feeds.base import TestBaseFeed
import pytest
from feedly.feeds.cassandraCQL import CassandraCQLFeed


@pytest.mark.usefixtures("cassandra_cql_reset")
class TestCassandraBaseFeed(TestBaseFeed):
    feed_cls = CassandraCQLFeed

    @pytest.skip
    def test_add_insert_activity(self):
        pass

    @pytest.skip
    def test_add_remove_activity(self):
        pass
