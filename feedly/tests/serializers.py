from feedly.aggregators.base import RecentVerbAggregator
from feedly.serializers.activity_serializer import ActivitySerializer
from feedly.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer, NotificationSerializer
from feedly.serializers.base import BaseSerializer
from feedly.serializers.pickle_serializer import PickleSerializer, \
    AggregatedActivityPickleSerializer
from feedly.tests.utils import FakeActivity
from functools import partial
import datetime
import unittest


class ActivitySerializationTest(unittest.TestCase):
    serialization_class = BaseSerializer

    def setUp(self):
        from feedly.verbs.base import Love as LoveVerb
        self.serializer = self.serialization_class()
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        aggregator = RecentVerbAggregator()
        self.aggregated_activity = aggregator.aggregate([self.activity])[0]
        self.args = ()
        self.kwargs = {}

    def test_serialization(self):
        serialized_activity = self.serializer.dumps(self.activity)
        deserialized_activity = self.serializer.loads(serialized_activity)
        self.assertEqual(deserialized_activity, self.activity)

    def test_type_exception(self):
        give_error = partial(self.serializer.dumps, 1)
        self.assertRaises(ValueError, give_error)
        give_error = partial(self.serializer.dumps, self.aggregated_activity)
        self.assertRaises(ValueError, give_error)


class PickleSerializationTestCase(ActivitySerializationTest):
    serialization_class = PickleSerializer


class ActivitySerializerTest(ActivitySerializationTest):
    serialization_class = ActivitySerializer


class AggregatedActivitySerializationTest(ActivitySerializationTest):
    serialization_class = AggregatedActivitySerializer

    def test_serialization(self):
        serialized = self.serializer.dumps(self.aggregated_activity)
        deserialized = self.serializer.loads(serialized)
        self.assertEqual(deserialized, self.aggregated_activity)

    def test_type_exception(self):
        give_error = partial(self.serializer.dumps, 1)
        self.assertRaises(ValueError, give_error)
        give_error = partial(self.serializer.dumps, self.activity)
        self.assertRaises(ValueError, give_error)

    def test_hydration(self):
        serialized_activity = self.serializer.dumps(self.aggregated_activity)
        deserialized_activity = self.serializer.loads(serialized_activity)
        assert self.serialization_class.dehydrate == deserialized_activity.dehydrated
        if deserialized_activity.dehydrated:
            assert not deserialized_activity.activities
            assert deserialized_activity._activity_ids


class PickleAggregatedActivityTest(AggregatedActivitySerializationTest):
    serialization_class = AggregatedActivityPickleSerializer


class NotificationSerializerTest(AggregatedActivitySerializationTest):
    serialization_class = NotificationSerializer
