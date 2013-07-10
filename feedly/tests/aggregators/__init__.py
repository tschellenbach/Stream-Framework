from feedly.aggregators.base import RecentVerbAggregator, NotificationAggregator
from feedly.feeds.aggregated_feed import AggregatedFeed, RedisAggregatedFeed
from feedly.feeds.memory import Feed
from feedly.tests.feeds.base import TestBaseFeed, implementation
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb, Add as AddVerb
import datetime
import unittest


class AggregatorTest(unittest.TestCase):
    aggregator_class = None
    
    def setUp(self):
        if self.aggregator_class is None:
            return
        self.user_id = 42
        self.activity = FakeActivity(1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        for x in range(10):
            activity_time = datetime.datetime.now()
            find = x > 5
            activity = FakeActivity(x, LoveVerb, 1, x, activity_time, dict(find=find))
            activities.append(activity)
        add_activities = []
        for x in range(25):
            activity_time = datetime.datetime.now()
            activity = FakeActivity(x, AddVerb, 1, x, activity_time, dict(x=x))
            add_activities.append(activity)
        self.activities = activities
        self.add_activities = add_activities
        self.aggregator = self.aggregator_class()
        
        
class RecentVerbAggregatorTest(AggregatorTest):
    aggregator_class = RecentVerbAggregator
    
    def test_aggregate(self):
        '''
        Verify that all the activities with the same verb and date are stuck
        together
        '''
        activities = self.activities + self.add_activities
        aggregated = self.aggregator.aggregate(activities)
        assert len(aggregated) == 2
        assert len(aggregated[0].activities) == 25
        assert len(aggregated[1].activities) == 10

    def test_empty_merge(self):
        activities = self.activities + self.add_activities
        aggregated = self.aggregator.aggregate(activities)
        new, changed = self.aggregator.merge([], aggregated)
        assert len(new) == 2
        assert len(new[0].activities) == 25
        assert len(new[1].activities) == 10
        
    def test_merge(self):
        first = self.aggregator.aggregate(self.activities[:5])
        second = self.aggregator.aggregate(self.activities[5:])
        new, changed = self.aggregator.merge(first, second)
        assert new == []
        
        old, updated = changed[0]
        assert len(old.activities) == 5
        assert len(updated.activities) == 10


class NotificationAggregatorTest(AggregatorTest):
    '''
    Same as RecentVerbAggregatorTest, but aggregates finds and loves differently
    '''
    aggregator_class = NotificationAggregator
    
    def test_aggregate(self):
        '''
        Verify that all the activities with the same verb and date are stuck
        together
        '''
        activities = self.activities + self.add_activities
        aggregated = self.aggregator.aggregate(activities)
        assert len(aggregated) == 3
        assert len(aggregated[0].activities) == 25
        assert len(aggregated[1].activities) == 4
        assert len(aggregated[2].activities) == 6

    def test_empty_merge(self):
        activities = self.activities + self.add_activities
        aggregated = self.aggregator.aggregate(activities)
        new, changed = self.aggregator.merge([], aggregated)
        assert len(new[0].activities) == 25
        assert len(new[1].activities) == 4
        assert len(new[2].activities) == 6
        
    def test_merge(self):
        first = self.aggregator.aggregate(self.activities[:2])
        second = self.aggregator.aggregate(self.activities[2:4])
        new, changed = self.aggregator.merge(first, second)
        assert new == []
        
        old, updated = changed[0]
        assert len(old.activities) == 2
        assert len(updated.activities) == 4
