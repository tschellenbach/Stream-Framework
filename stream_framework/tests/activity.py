import datetime
from stream_framework.activity import Activity
from stream_framework.activity import AggregatedActivity
from stream_framework.activity import DehydratedActivity
from stream_framework.tests.utils import Pin
from stream_framework.verbs.base import Love as LoveVerb
from stream_framework.aggregators.base import RecentVerbAggregator
from stream_framework.exceptions import ActivityNotFound
from stream_framework.exceptions import DuplicateActivityException
import time
import unittest
import six


class TestActivity(unittest.TestCase):

    def test_serialization_length(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        assert len(str(activity.serialization_id)) == 26

    def test_serialization_type(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        assert isinstance(activity.serialization_id, (six.integer_types, float))

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

    def test_dehydrated_activity(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        dehydrated = activity.get_dehydrated()
        self.assertTrue(isinstance(dehydrated, DehydratedActivity))
        self.assertEquals(
            dehydrated.serialization_id, activity.serialization_id)

    def test_compare_idempotent_init(self):
        t1 = datetime.datetime.utcnow()
        activity_object = Pin(id=1)
        activity1 = Activity(1, LoveVerb, activity_object, time=t1)
        time.sleep(0.1)
        activity2 = Activity(1, LoveVerb, activity_object, time=t1)
        self.assertEquals(activity1, activity2)

    def test_compare_apple_and_oranges(self):
        activity_object = Pin(id=1)
        activity = Activity(1, LoveVerb, activity_object)
        with self.assertRaises(ValueError):
            activity == activity_object


class TestAggregatedActivity(unittest.TestCase):

    def test_contains(self):
        activity = Activity(1, LoveVerb, Pin(id=1))
        aggregated = AggregatedActivity(1, [activity])
        self.assertTrue(aggregated.contains(activity))

    def test_duplicated_activities(self):
        activity = Activity(1, LoveVerb, Pin(id=1))
        aggregated = AggregatedActivity(1, [activity])
        with self.assertRaises(DuplicateActivityException):
            aggregated.append(activity)

    def test_compare_apple_and_oranges(self):
        activity = AggregatedActivity(1, [Activity(1, LoveVerb, Pin(id=1))])
        with self.assertRaises(ValueError):
            activity == Pin(id=1)

    def test_contains_extraneous_object(self):
        activity = AggregatedActivity(1, [Activity(1, LoveVerb, Pin(id=1))])
        with self.assertRaises(ValueError):
            activity.contains(Pin(id=1))

    def test_aggregated_properties(self):
        activities = []
        for x in range(1, 101):
            activity_object = Pin(id=x)
            activity = Activity(x, LoveVerb, activity_object)
            activities.append(activity)
        aggregator = RecentVerbAggregator()
        aggregated_activities = aggregator.aggregate(activities)
        aggregated = aggregated_activities[0]

        self.assertEqual(aggregated.verbs, [LoveVerb])
        self.assertEqual(aggregated.verb, LoveVerb)
        self.assertEqual(aggregated.actor_count, 100)
        self.assertEqual(aggregated.minimized_activities, 85)
        self.assertEqual(aggregated.other_actor_count, 99)
        self.assertEqual(aggregated.activity_count, 100)
        self.assertEqual(aggregated.object_ids, list(range(86, 101)))
        # the other ones should be dropped
        self.assertEqual(aggregated.actor_ids, list(range(86, 101)))
        self.assertEqual(aggregated.is_seen(), False)
        self.assertEqual(aggregated.is_read(), False)

    def generate_activities(self):
        activities = []
        for x in range(1, 20):
            activity = Activity(x, LoveVerb, Pin(id=x))
            activities.append(activity)
        return activities

    def generate_aggregated_activities(self, activities):
        aggregator = RecentVerbAggregator()
        aggregated_activities = aggregator.aggregate(activities)
        return aggregated_activities

    def test_aggregated_compare(self):
        activities = self.generate_activities()
        aggregated_activities = self.generate_aggregated_activities(activities)
        aggregated_activities_two = self.generate_aggregated_activities(activities)

        new_activities = self.generate_activities()
        aggregated_activities_three = self.generate_aggregated_activities(new_activities)

        # this should be equal
        self.assertEqual(aggregated_activities, aggregated_activities_two)
        # this should not be equal
        self.assertNotEqual(aggregated_activities, aggregated_activities_three)

    def test_aggregated_remove(self):
        activities = []
        for x in range(1, 101):
            activity_object = Pin(id=x)
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
