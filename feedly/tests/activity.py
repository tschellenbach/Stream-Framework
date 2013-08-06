from feedly.activity import Activity
from feedly.tests.utils import Pin
from feedly.verbs.base import Love as LoveVerb
import unittest
from feedly.aggregators.base import RecentVerbAggregator
from feedly.exceptions import ActivityNotFound


class TestActivity(unittest.TestCase):

    def test_serialization_length(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        assert len(str(activity.serialization_id)) == 26

    def test_serialization_type(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        assert isinstance(activity.serialization_id, (int, long, float))

    def test_serialization_overflow_check_object_id(self):
        activity_object = Pin(id=10 ** 10)
        activity = Activity(1, LoveVerb, activity_object)
        with self.assertRaises(TypeError):
            activity.serialization_id

    def test_serialization_overflow_check_role_id(self):
        activity_object = Pin(id=1)
        Verb = type('Overflow', (LoveVerb,), {'id': 9999})
        activity = Activity(1, Verb, activity_object)
        with self.assertRaises(TypeError):
            activity.serialization_id


class TestAggregatedActivity(unittest.TestCase):

    def test_aggregated_properties(self):
        activity_object = Pin(id=1)
        activities = []
        for x in range(1, 101):
            activity = Activity(x, LoveVerb, activity_object)
            activities.append(activity)
        aggregator = RecentVerbAggregator()
        aggregated_activities = aggregator.aggregate(activities)
        aggregated = aggregated_activities[0]

        self.assertEqual(aggregated.verbs, [LoveVerb])
        self.assertEqual(aggregated.verb, LoveVerb)
        self.assertEqual(aggregated.actor_count, 100)
        self.assertEqual(aggregated.minimized_activities, 85)
        self.assertEqual(aggregated.other_actor_count, 98)
        self.assertEqual(aggregated.activity_count, 100)
        self.assertEqual(aggregated.object_ids, [1])
        # the other ones should be dropped
        self.assertEqual(aggregated.actor_ids, range(86, 101))
        self.assertEqual(aggregated.is_seen(), False)
        self.assertEqual(aggregated.is_read(), False)
        rep = repr(aggregated)

    def generate_aggregated_activities(self, diff=0):
        aggregator = RecentVerbAggregator()
        activity_object = Pin(id=1)
        activities = []
        for x in range(1, 20 + diff):
            activity = Activity(x, LoveVerb, activity_object)
            activities.append(activity)
        aggregated_activities = aggregator.aggregate(activities)
        return aggregated_activities

    def test_aggregated_compare(self):
        return
        aggregated_activities = self.generate_aggregated_activities()
        aggregated_activities_two = self.generate_aggregated_activities()
        aggregated_activities_three = self.generate_aggregated_activities(3)

        # this should be equal
        self.assertEqual(aggregated_activities, aggregated_activities_two)
        # this should not be equal
        self.assertNotEqual(aggregated_activities, aggregated_activities_three)

    def test_aggregated_remove(self):
        activity_object = Pin(id=1)
        activities = []
        for x in range(1, 101):
            activity = Activity(x, LoveVerb, activity_object)
            activities.append(activity)
        aggregator = RecentVerbAggregator()
        aggregated_activities = aggregator.aggregate(activities)
        aggregated = aggregated_activities[0]
        for activity in activities:
            try:
                aggregated.remove(activity)
            except (ActivityNotFound, ValueError):
                pass
        self.assertEqual(len(aggregated.activities), 1)
        self.assertEqual(aggregated.activity_count, 72)
