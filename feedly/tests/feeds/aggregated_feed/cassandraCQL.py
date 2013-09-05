from feedly.feeds.aggregated_feed.cassandraCQL import CassandraAggregatedFeed
from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed
import pytest


@pytest.mark.usefixtures("cassandra_cql_reset")
class TestCassandraAggregatedFeed(TestAggregatedFeed):
    feed_cls = CassandraAggregatedFeed
