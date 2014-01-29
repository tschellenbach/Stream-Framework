from feedly.aggregators.base import RecentVerbAggregator
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb, Add as AddVerb
import datetime
import unittest


class AggregatorTest(unittest.TestCase):
    aggregator_class = None

    def setUp(self):
        id_seq = range(42, 999)
        if self.aggregator_class is None:
            return

        self.user_id = 42
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        self.activities = []
        for x in range(2, 12):
            activity_time = datetime.datetime.now()
            find = x > 5
            activity = FakeActivity(
                x, LoveVerb, id_seq.pop(), x, activity_time, dict(find=find))
            self.activities.append(activity)
        self.add_activities = []
        for x in range(13, 38):
            activity_time = datetime.datetime.now() + datetime.timedelta(
                seconds=x)
            activity = FakeActivity(
                x, AddVerb, id_seq.pop(), x, activity_time, dict(x=x))
            self.add_activities.append(activity)
        self.aggregator = self.aggregator_class()


class RecentVerbAggregatorTest(AggregatorTest):
    aggregator_class = RecentVerbAggregator

    def test_aggregate(self):
        '''
        Verify that all the activities with the same verb and date are stuck
        together
        '''
        assert len(self.activities) == 10
        assert len(self.add_activities) == 25
        activities = self.activities + self.add_activities
        aggregated = self.aggregator.aggregate(activities)
        assert len(aggregated) == 2
        assert len(aggregated[0].activities) == 15
        assert len(aggregated[1].activities) == 10

    def test_empty_merge(self):
        activities = self.activities + self.add_activities
        new, changed, deleted = self.aggregator.merge([], activities)
        assert len(new) == 2
        assert len(new[0].activities) == 15
        assert len(new[1].activities) == 10

    def test_merge(self):
        first = self.aggregator.aggregate(self.activities[:5])
        new, changed, deleted = self.aggregator.merge(
            first, self.activities[5:])
        assert new == []

        old, updated = changed[0]
        assert len(old.activities) == 5
        assert len(updated.activities) == 10
