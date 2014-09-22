from feedly.activity import AggregatedActivity
from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed
from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed,\
    implementation
from feedly.tests.feeds.cassandra import CustomActivity
import pytest


class CustomAggregated(AggregatedActivity):
    pass


class CassandraCustomAggregatedFeed(CassandraAggregatedFeed):
    activity_class = CustomActivity
    aggregated_activity_class = CustomAggregated


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraAggregatedFeed(TestAggregatedFeed):
    feed_cls = CassandraAggregatedFeed


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraCustomAggregatedFeed(TestAggregatedFeed):
    feed_cls = CassandraCustomAggregatedFeed
    activity_class = CustomActivity
    aggregated_activity_class = CustomAggregated

    @implementation
    def test_custom_activity(self):
        assert self.test_feed.count() == 0
        self.feed_cls.insert_activity(
            self.activity
        )
        self.test_feed.add(self.activity)
        assert self.test_feed.count() == 1
        aggregated = self.test_feed[:10][0]
        assert type(aggregated) == self.aggregated_activity_class
        assert type(aggregated.activities[0]) == self.activity_class
