from feedly.tests.feeds.base import TestBaseFeed, implementation
from feedly.feeds.memory import Feed
from feedly.feeds.aggregated_feed import AggregatedFeed, RedisAggregatedFeed
from feedly.aggregators.base import RecentVerbAggregator
from feedly.tests.utils import FakeActivity
import datetime
import unittest
from feedly.verbs.base import Love as LoveVerb


class TestAggregatedFeed(unittest.TestCase):
    feed_cls = RedisAggregatedFeed
    timeline_storage_options = {}
    activity_storage_options = {}

    def setUp(self):
        self.user_id = 42
        self.test_feed = self.feed_cls(
            self.user_id,
            'feed_%(user_id)s',
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )
        self.activity = FakeActivity(1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        for x in range(10):
            activity_time = datetime.datetime.now() + datetime.timedelta(hours=1)
            activity = FakeActivity(x, LoveVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        self.activities = activities

    def tearDown(self):
        self.test_feed.activity_storage.flush()
        self.test_feed.delete()

    def test_aggregated_feed(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        # test by sticking the items in the feed
        for activity in self.activities:
            self.test_feed.add(activity)
        results = self.test_feed[:10]
        # compare it to a direct call on the aggregator
        aggregator = self.test_feed.get_aggregator()
        aggregated_activities = aggregator.aggregate(self.activities)
        print results
        # check the feed
        assert results == aggregated_activities
        

