from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.memory import Feed
from feedly.feeds.aggregated_feed import AggregatedFeed, RedisAggregatedFeed
from feedly.aggregators.base import RecentVerbAggregator


class TestBaseAggregatedFeed(TestBaseFeed):
    pass


class TestAggregatedFeed(TestBaseAggregatedFeed):
    feed_cls = RedisAggregatedFeed

    def test_aggregated_feed(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        # test by sticking the items in the feed
        self.test_feed.add_many(self.activities)
        results = self.test_feed[:10]
        # compare it to a direct call on the aggregator
        aggregator = self.test_feed.get_aggregator()
        aggregated_activities = aggregator.aggregate(self.activities)
        # check the feed
        print aggregated_activities
        print results
        assert results == aggregated_activities

