from feedly.tests.feeds.base import TestBaseFeed, implementation
from feedly.feeds.memory import Feed
from feedly.feeds.aggregated_feed import AggregatedFeed, RedisAggregatedFeed
from feedly.aggregators.base import RecentVerbAggregator
from feedly.tests.utils import FakeActivity
import datetime


class TestAggregatedFeed(TestBaseFeed):
    feed_cls = RedisAggregatedFeed

    def test_aggregated_feed(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        # test by sticking the items in the feed
        for activity in self.activities:
            self.feed_cls.insert_activity(
                activity,
                **self.activity_storage_options
            )
            self.test_feed.add(activity.serialization_id)
        results = self.test_feed[:10]
        # compare it to a direct call on the aggregator
        aggregator = self.test_feed.get_aggregator()
        aggregated_activities = aggregator.aggregate(self.activities)
        # check the feed
        assert results == aggregated_activities
        

