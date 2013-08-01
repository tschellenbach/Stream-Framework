from feedly.feeds.aggregated_feed.base import AggregatedFeed
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb
import datetime
import unittest
from feedly.verbs.base import Add as AddVerb
import random


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.feed_cls == AggregatedFeed:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class TestAggregatedFeed(unittest.TestCase):
    feed_cls = AggregatedFeed

    def setUp(self):
        self.user_id = 42
        self.test_feed = self.feed_cls(self.user_id)
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=1)
        for x in range(1, 10):
            activity_time = base_time + datetime.timedelta(
                hours=x)
            activity = FakeActivity(
                x, LoveVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        self.activities = activities
        aggregator = self.test_feed.get_aggregator()
        self.aggregated = aggregator.aggregate(activities)[0]
        if self.__class__ != TestAggregatedFeed:
            self.test_feed.delete()

    def tearDown(self):
        if self.feed_cls != AggregatedFeed:
            self.test_feed.delete()

    @implementation
    def test_add_aggregated_activity(self):
        # start by adding one
        self.test_feed.insert_activities(self.aggregated.activities)
        self.test_feed.add_many_aggregated([self.aggregated])
        assert len(self.test_feed[:10]) == 1

    @implementation
    def test_slicing(self):
        # start by adding one
        self.test_feed.insert_activities(self.aggregated.activities)
        self.test_feed.add_many_aggregated([self.aggregated])
        assert len(self.test_feed[:10]) == 1

        assert len(self.test_feed[:]) == 1

    @implementation
    def test_remove_aggregated_activity(self):
        # start by adding one
        self.test_feed.insert_activities(self.aggregated.activities)
        self.test_feed.add_many_aggregated([self.aggregated])
        assert len(self.test_feed[:10]) == 1
        # now remove it
        self.test_feed.remove_many_aggregated([self.aggregated])
        assert len(self.test_feed[:10]) == 0

    @implementation
    def test_add_activity(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        # test by sticking the items in the feed
        for activity in self.activities:
            self.test_feed.insert_activity(activity)
            self.test_feed.add(activity)
        results = self.test_feed[:3]
        # compare it to a direct call on the aggregator
        aggregator = self.test_feed.get_aggregator()
        aggregated_activities = aggregator.aggregate(self.activities)
        # check the feed
        assert results[0].actor_ids == aggregated_activities[0].actor_ids

    @implementation
    def test_contains(self):
        # test by sticking the items in the feed
        self.test_feed.insert_activities(self.activities)
        self.test_feed.add_many(self.activities)
        
        for activity in self.activities:
            contains = self.test_feed.contains(activity)
            self.assertTrue(contains)

    @implementation
    def test_remove_activity(self):
        assert len(self.test_feed[:10]) == 0
        # test by sticking the items in the feed
        activity = self.activities[0]
        self.test_feed.insert_activity(activity)
        self.test_feed.add(activity)
        assert len(self.test_feed[:10]) == 1
        assert len(self.test_feed[:10][0].activities) == 1
        # now remove the activity
        self.test_feed.remove(activity)
        assert len(self.test_feed[:10]) == 0

    @implementation
    def test_partially_remove_activity(self):
        assert len(self.test_feed[:10]) == 0
        # test by sticking the items in the feed
        activities = self.activities[:2]
        for activity in activities:
            self.test_feed.insert_activity(activity)
            self.test_feed.add(activity)
        assert len(self.test_feed[:10]) == 1
        assert len(self.test_feed[:10][0].activities) == 2
        # now remove the activity
        self.test_feed.remove(activity)
        assert len(self.test_feed[:10]) == 1
        assert len(self.test_feed[:10][0].activities) == 1

    @implementation
    def test_add_many_and_trim(self):
        activities = []
        choices = [LoveVerb, AddVerb]
        for i in range(1, 50):
            verb = choices[i % 2]
            activity = FakeActivity(
                i, verb, i, i, datetime.datetime.now() - datetime.timedelta(seconds=i))
            activities.append(activity)

        self.test_feed.insert_activities(activities)
        self.test_feed.add_many(activities)
        # now test the trim
        self.assertEqual(self.test_feed.count(), 2)
        self.test_feed.trim(1)
        self.assertEqual(self.test_feed.count(), 1)
