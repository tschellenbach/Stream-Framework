import unittest
from feedly.feeds.aggregated_feed.realtime import RealTimeAggregatedFeed
from feedly.feeds.redis import RedisFeed
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb
from feedly.verbs.base import Add as AddVerb
from feedly.verbs.base import Follow as FollowVerb
import datetime
from random import choice
from random import shuffle


class TestRealTimeAggregatedFeed(RealTimeAggregatedFeed):
    source_feed_class = RedisFeed


class TestRealtimeAggregatedFeed(unittest.TestCase):

    def setUp(self):
        self.user_id = 42
        self.test_feed = TestRealTimeAggregatedFeed(self.user_id)
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=10)
        activity_verbs = [LoveVerb, AddVerb, FollowVerb] * 1000
        shuffle(activity_verbs)

        for i, verb in enumerate(activity_verbs):
            activity_time = base_time + datetime.timedelta(
                minutes=i*choice([15,20]))
            activity = FakeActivity(
                i, verb, 1, i, activity_time, dict(i=i))
            activities.append(activity)

        self.activities = activities
        self.test_feed.feed.delete()
        self.test_feed.prefetch_ratio = 10
        self.test_feed.max_read_attempts = 3
        self.test_feed.feed.insert_activities(self.activities)
        self.test_feed.feed.add_many(self.activities)

    def test_add_aggregated_activity(self):
        assert len(self.test_feed[:10]) == 10
        assert len(self.test_feed[:5]) == 5

    def test_offset_unsupported(self):
        with self.assertRaises(TypeError):
            self.test_feed[4:8]

    def test_add_aggregated_activity_big_prefetch(self):
        self.test_feed.prefetch_ratio = 100
        assert len(self.test_feed[:10]) == 10
        assert len(self.test_feed[:5]) == 5

    def test_slicing(self):
        assert len(self.test_feed[:10]) == 10
        assert len(self.test_feed[:]) > 10

    def test_filter(self):
        assert self.test_feed.feed._filter_kwargs == {}
        filtered = self.test_feed.filter(id__lte=12)
        assert self.test_feed.feed._filter_kwargs == {}
        assert filtered.feed._filter_kwargs == {'id__lte': 12}
