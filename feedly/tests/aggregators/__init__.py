from feedly.aggregators.base import RecentVerbAggregator, FashiolistaAggregator
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
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        activities = []
        for x in range(10):
            activity_time = datetime.datetime.now()
            find = x > 5
            activity = FakeActivity(
                x, LoveVerb, 1, x, activity_time, dict(find=find))
            activities.append(activity)
        add_activities = []
        for x in range(25):
            activity_time = datetime.datetime.now() + datetime.timedelta(seconds=4)
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
        new, changed, deleted = self.aggregator.merge([], aggregated)
        assert len(new) == 2
        assert len(new[0].activities) == 25
        assert len(new[1].activities) == 10

    def test_merge(self):
        first = self.aggregator.aggregate(self.activities[:5])
        second = self.aggregator.aggregate(self.activities[5:])
        new, changed, deleted = self.aggregator.merge(first, second)
        assert new == []

        old, updated = changed[0]
        assert len(old.activities) == 5
        assert len(updated.activities) == 10


class FashiolistaAggregatorTest(AggregatorTest):
    aggregator_class = FashiolistaAggregator

    def setUp(self):
        if self.aggregator_class is None:
            return
        self.user_id = 42

        # loves to be aggregated by entity
        self.agg_entity_loves = []  # 0,1,2,3,4,5,6,7,8,9,10
        for i, entity_id in enumerate([1, 2, 3, 3, 3, 4, 5, 6, 6, 6, 6]):
            self.agg_entity_loves.append(
                FakeActivity(
                    i, LoveVerb, entity_id, time=datetime.datetime.now())
            )

        # loves to be aggregated by user
        self.agg_user_loves = []  # 0,1,2,3,4,5,6,7,8,9,10
        for i, user_id in enumerate([1, 2, 3, 3, 3, 4, 5, 6, 6, 6, 6]):
            self.agg_user_loves.append(
                FakeActivity(
                    user_id, LoveVerb, i, time=datetime.datetime.now())
            )

        # loves to be mixed agregated
        self.agg_mixed_loves = []
        user_ids = [1, 1, 1, 2, 3, 4, 5]
        entity_ids = [5, 6, 7, 8, 8, 8, 9]
        for i, user_id in enumerate(user_ids):
            self.agg_mixed_loves.append(
                FakeActivity(user_id, LoveVerb, entity_ids[
                             i], time=datetime.datetime.now())
            )

        self.aggregator = self.aggregator_class()

    def test_entity_aggregate(self):
        '''
        Verify that all the activities with the same entity & >1 loves per hour are stuck
        together
        '''

        aggregated = self.aggregator.aggregate(self.agg_entity_loves)

        assert len(aggregated) == 6
        assert len(aggregated[0].activities) == 1
        assert len(aggregated[1].activities) == 1
        assert len(aggregated[2].activities) == 3
        assert len(aggregated[3].activities) == 1
        assert len(aggregated[4].activities) == 1
        assert len(aggregated[5].activities) == 4

    def test_user_aggregate(self):
        '''
        Verify that all the activities with the same user and hour are stuck
        together
        '''

        aggregated = self.aggregator.aggregate(self.agg_user_loves)

        assert len(aggregated) == 6
        assert len(aggregated[0].activities) == 1
        assert len(aggregated[1].activities) == 1
        assert len(aggregated[2].activities) == 3
        assert len(aggregated[3].activities) == 1
        assert len(aggregated[4].activities) == 1
        assert len(aggregated[5].activities) == 4

    def test_mixed_aggregate(self):
        '''
        Verify that all the activities with the same user and hour are stuck
        together
        '''

        aggregated = self.aggregator.aggregate(self.agg_mixed_loves)

        assert len(aggregated) == 3
        assert len(aggregated[0].activities) == 3
        assert len(aggregated[1].activities) == 3
        assert len(aggregated[2].activities) == 1

    def test_empty_merge(self):
        aggregated = self.aggregator.aggregate(self.agg_user_loves)
        new, changed, deleted = self.aggregator.merge([], aggregated)
        assert len(new) == 6
        assert len(aggregated[0].activities) == 1
        assert len(aggregated[1].activities) == 1
        assert len(aggregated[2].activities) == 3
        assert len(aggregated[3].activities) == 1
        assert len(aggregated[4].activities) == 1
        assert len(aggregated[5].activities) == 4

    def test_merge_add_to_user_agg(self):
        first = self.aggregator.aggregate(self.agg_mixed_loves)
        second = self.aggregator.aggregate(
            [FakeActivity(1, LoveVerb, 10, time=datetime.datetime.now())])

        new, changed, deleted = self.aggregator.merge(first, second)

        assert new == deleted == []

        old, updated = changed[0]
        assert len(old.activities) == 3
        assert len(updated.activities) == 4

    def test_merge_add_to_entity_agg(self):
        first = self.aggregator.aggregate(self.agg_mixed_loves)
        second = self.aggregator.aggregate(
            [FakeActivity(6, LoveVerb, 8, time=datetime.datetime.now())])

        new, changed, deleted = self.aggregator.merge(first, second)

        assert new == deleted == []

        old, updated = changed[0]
        assert len(old.activities) == 3
        assert len(updated.activities) == 4

    def test_merge_new_agg(self):
        first = self.aggregator.aggregate(self.agg_mixed_loves)
        second = self.aggregator.aggregate(
            [FakeActivity(666, LoveVerb, 666, time=datetime.datetime.now())])

        new, changed, deleted = self.aggregator.merge(first, second)

        assert len(new) == 1
        assert changed == deleted == []

        assert len(new[0].activities) == 1

    def test_merge_deleted_agg(self):
        first = self.aggregator.aggregate(self.agg_mixed_loves)
        second = self.aggregator.aggregate(
            [FakeActivity(6, LoveVerb, 9, time=datetime.datetime.now())])

        new, changed, deleted = self.aggregator.merge(first, second)

        assert len(deleted) == len(new) == 1
        assert changed == []

        assert len(deleted[0].activities) == 1
        assert len(new[0].activities) == 2
