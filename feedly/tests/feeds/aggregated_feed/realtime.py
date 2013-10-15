import unittest
from feedly.feeds.aggregated_feed.realtime import RealTimeAggregatedFeed
from feedly.feeds.redis import RedisFeed
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb
from feedly.verbs.base import Add as AddVerb
import datetime


class TestRealTimeAggregatedFeed(RealTimeAggregatedFeed):
    source_feed_class = RedisFeed


class TestRedisAggregatedFeed(unittest.TestCase):

    def setUp(self):
        self.user_id = 42
        self.test_feed = TestRealTimeAggregatedFeed(self.user_id)
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=10)
        for x in range(1, 10):
            activity_time = base_time + datetime.timedelta(
                hours=x)
            activity = FakeActivity(
                x, LoveVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        for x in range(20, 30):
            activity_time = base_time + datetime.timedelta(
                hours=x)
            activity = FakeActivity(
                x, AddVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        self.activities = activities
        self.test_feed.feed.delete()

    def test_add_aggregated_activity(self):
        self.test_feed.feed.insert_activities(self.activities)
        self.test_feed.feed.add_many(self.activities)
        assert len(self.test_feed[:10]) == 2

    def test_slicing(self):
        self.test_feed.feed.insert_activities(self.activities)
        self.test_feed.feed.add_many(self.activities)
        assert len(self.test_feed[:10]) == 2
        assert len(self.test_feed[:]) == 2

    def test_filter(self):
        assert self.test_feed.feed._filter_kwargs == {}
        filtered = self.test_feed.filter(id__lte=12)
        assert self.test_feed.feed._filter_kwargs == {}
        assert filtered.feed._filter_kwargs == {'id__lte': 12}
