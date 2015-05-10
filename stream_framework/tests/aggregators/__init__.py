from __future__ import division
import datetime
import unittest
from stream_framework.aggregators.base import RecentVerbAggregator, NotificationAggregator
from stream_framework.tests.utils import FakeActivity
from stream_framework.verbs.base import Love as LoveVerb, Comment as CommentVerb


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.aggregator_class is None:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class BaseAggregatorTest(unittest.TestCase):

    aggregator_class = None
    # Defines a list of activities that will be merged into one group
    first_activities_group = []
    # Another list of activities that will be merged into a second group
    second_activities_group = []

    @property
    def today(self):
        return datetime.datetime.now().replace(minute=0)

    @property
    def yesterday(self):
        return self.today - datetime.timedelta(days=1)

    @implementation
    def test_aggregate(self):
        aggregator = self.aggregator_class()
        activities = self.first_activities_group + self.second_activities_group
        aggregated = aggregator.aggregate(activities)
        self.assertEqual(len(aggregated), 2)
        self.assertEqual(aggregated[0].activities, self.first_activities_group)
        self.assertEqual(aggregated[1].activities, self.second_activities_group)

    @implementation
    def test_empty_merge(self):
        aggregator = self.aggregator_class()
        activities = self.first_activities_group + self.second_activities_group
        new, changed, deleted = aggregator.merge([], activities)
        self.assertEqual(len(new), 2)
        self.assertEqual(new[0].activities, self.first_activities_group)
        self.assertEqual(new[1].activities, self.second_activities_group)
        self.assertEqual(len(changed), 0)
        self.assertEqual(len(deleted), 0)

    @implementation
    def test_merge(self):
        aggregator = self.aggregator_class()
        middle_index = len(self.first_activities_group) // 2
        first = aggregator.aggregate(self.first_activities_group[:middle_index])
        new, changed, deleted = aggregator.merge(first,
                                                 self.first_activities_group[middle_index:])
        self.assertEqual(len(new), 0)
        self.assertEqual(len(deleted), 0)

        old, updated = changed[0]
        self.assertEqual(old.activities, self.first_activities_group[:middle_index])
        self.assertEqual(updated.activities, self.first_activities_group)


class BaseRecentVerbAggregatorTest(BaseAggregatorTest):

    id_seq = list(range(42, 999))

    def create_activities(self, verb, creation_date, count):
        return [FakeActivity(actor = x,
                             verb = verb,
                             object = self.id_seq.pop(),
                             target = x,
                             time = creation_date + datetime.timedelta(seconds=x),
                             extra_context = dict(x=x))
                for x in range(0, count)]


class RecentVerbAggregatorVerbTest(BaseRecentVerbAggregatorTest):
    '''
    Tests that activities are aggregated by same verbs
    '''

    aggregator_class = RecentVerbAggregator

    def setUp(self):
        self.first_activities_group = self.create_activities(LoveVerb, self.today, 10)
        self.second_activities_group = self.create_activities(CommentVerb, self.today, 5)


class RecentVerbAggregatorDateTest(BaseRecentVerbAggregatorTest):
    '''
    Tests that activities are aggregated by same date
    '''

    aggregator_class = RecentVerbAggregator

    def setUp(self):
        self.first_activities_group = self.create_activities(LoveVerb, self.today, 10)
        self.second_activities_group = self.create_activities(LoveVerb, self.yesterday, 5)


class BaseNotificationAggregatorTest(BaseAggregatorTest):

    first_item_id = 1000000
    second_item_id = 20000000

    def create_activities(self, verb, object_id, creation_date, count):
        return [FakeActivity(actor = x,
                             verb = verb,
                             object = object_id,
                             target = x,
                             time=creation_date + datetime.timedelta(seconds=x),
                             extra_context = dict(x=x))
                for x in range(0, count)]


class NotificationAggregatorVerbTest(BaseNotificationAggregatorTest):
    '''
    Tests that activities are aggregated by same verbs
    '''

    aggregator_class = NotificationAggregator

    def setUp(self):
        self.first_activities_group = self.create_activities(LoveVerb, self.first_item_id, self.today, 10)
        self.second_activities_group = self.create_activities(CommentVerb, self.first_item_id, self.today, 5)


class NotificationAggregatorObjectTest(BaseNotificationAggregatorTest):
    '''
    Tests that activities are aggregated by same object
    '''

    aggregator_class = NotificationAggregator

    def setUp(self):
        self.first_activities_group = self.create_activities(LoveVerb, self.first_item_id, self.today, 10)
        self.second_activities_group = self.create_activities(LoveVerb, self.second_item_id, self.today, 5)


class NotificationAggregatorDateTest(BaseNotificationAggregatorTest):
    '''
    Tests that activities are aggregated by same day
    '''

    aggregator_class = NotificationAggregator

    def setUp(self):
        self.first_activities_group = self.create_activities(LoveVerb, self.first_item_id, self.today, 10)
        self.second_activities_group = self.create_activities(LoveVerb, self.first_item_id, self.yesterday, 5)
