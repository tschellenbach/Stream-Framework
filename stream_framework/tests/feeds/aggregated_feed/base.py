from stream_framework.activity import Activity, AggregatedActivity
from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.feeds.notification_feed.base import BaseNotificationFeed
from stream_framework.verbs.base import Add as AddVerb, Love as LoveVerb
import copy
import datetime
import unittest
import time


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.feed_cls in (AggregatedFeed, BaseNotificationFeed):
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class TestAggregatedFeed(unittest.TestCase):
    feed_cls = AggregatedFeed
    activity_class = Activity
    aggregated_activity_class = AggregatedActivity

    def setUp(self):
        self.user_id = 42
        self.test_feed = self.feed_cls(self.user_id)
        self.activity = self.activity_class(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=10)
        # make sure that the first portion of activities are created within the same day
        base_time = base_time.replace(hour=0)
        for x in range(1, 10):
            activity_time = base_time + datetime.timedelta(
                hours=x)
            activity = self.activity_class(
                x, LoveVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        for x in range(20, 30):
            activity_time = base_time + datetime.timedelta(
                hours=x)
            activity = self.activity_class(
                x, AddVerb, 1, x, activity_time, dict(x=x))
            activities.append(activity)
        self.activities = activities
        aggregator = self.test_feed.get_aggregator()
        self.aggregated_activities = aggregator.aggregate(activities)
        self.aggregated = self.aggregated_activities[0]

    def tearDown(self):
        if self.feed_cls not in (AggregatedFeed, BaseNotificationFeed):
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
    def test_translate_diff(self):
        new = [self.aggregated_activities[0]]
        deleted = [self.aggregated_activities[1]]
        from_aggregated = copy.deepcopy(self.aggregated_activities[1])
        from_aggregated.seen_at = datetime.datetime.now()
        to_aggregated = copy.deepcopy(from_aggregated)
        to_aggregated.seen_at = None
        changed = [(from_aggregated, to_aggregated)]
        to_remove, to_add = self.test_feed._translate_diff(
            new, changed, deleted)

        correct_to_remove = [self.aggregated_activities[1], from_aggregated]
        correct_to_add = [self.aggregated_activities[0], to_aggregated]
        self.assertEqual(to_remove, correct_to_remove)
        self.assertEqual(to_add, correct_to_add)

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
        few_activities = self.activities[:10]
        self.test_feed.insert_activities(few_activities)
        self.test_feed.add_many(few_activities)

        for activity in few_activities:
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
    def test_large_remove_activity(self):
        # first built a large feed
        self.test_feed.max_length = 3600
        activities = []
        choices = [LoveVerb, AddVerb]
        for i in range(1, 3600):
            verb = choices[i % 2]
            activity = self.activity_class(
                i, verb, i, i, datetime.datetime.now() - datetime.timedelta(days=i))
            activities.append(activity)
        self.test_feed.insert_activities(activities)
        self.test_feed.add_many(activities)

        to_remove = activities[200:700]
        self.test_feed.remove_many(to_remove)

    @implementation
    def test_add_many_and_trim(self):
        activities = []
        choices = [LoveVerb, AddVerb]
        for i in range(1, 51):
            verb = choices[i % 2]
            activity = self.activity_class(
                i, verb, i, i, datetime.datetime.now() + datetime.timedelta(days=i))
            activities.append(activity)

        self.test_feed.insert_activities(activities)
        for activity in activities:
            time.sleep(0.01)
            self.test_feed.add_many([activity])

        self.test_feed[1:3]
        # now test the trim
        self.assertEqual(self.test_feed.count(), 50)
        self.test_feed.trim(3)
        self.assertEqual(self.test_feed.count(), 3)
