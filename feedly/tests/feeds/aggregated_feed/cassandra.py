from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed
from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed
import pytest


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraAggregatedFeed(TestAggregatedFeed):
    feed_cls = CassandraAggregatedFeed
