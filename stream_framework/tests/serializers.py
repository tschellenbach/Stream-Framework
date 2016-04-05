from stream_framework.aggregators.base import RecentVerbAggregator
from stream_framework.serializers.activity_serializer import ActivitySerializer
from stream_framework.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer, NotificationSerializer
from stream_framework.serializers.base import BaseSerializer
from stream_framework.serializers.cassandra.activity_serializer import CassandraActivitySerializer
from stream_framework.serializers.pickle_serializer import PickleSerializer, \
    AggregatedActivityPickleSerializer
from stream_framework.storage.cassandra import models
from stream_framework.tests.utils import FakeActivity
from functools import partial
import datetime
import unittest
from stream_framework.activity import Activity, AggregatedActivity


class ActivitySerializationTest(unittest.TestCase):
    serialization_class = BaseSerializer
    serialization_class_kwargs = {
        'activity_class': Activity, 'aggregated_activity_class': AggregatedActivity}
    activity_extra_context = {'xxx': 'yyy'}

    def setUp(self):
        from stream_framework.verbs.base import Love as LoveVerb
        self.serializer = self.serialization_class(
            **self.serialization_class_kwargs)
        self.activity = FakeActivity(
            1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        self.activity.extra_context = self.activity_extra_context
        aggregator = RecentVerbAggregator()
        self.aggregated_activity = aggregator.aggregate([self.activity])[0]
        self.args = ()
        self.kwargs = {}

    def test_serialization(self):
        serialized_activity = self.serializer.dumps(self.activity)
        deserialized_activity = self.serializer.loads(serialized_activity)
        self.assertEqual(deserialized_activity, self.activity)
        self.assertEqual(
            deserialized_activity.extra_context, self.activity_extra_context)

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


# class CassandraActivitySerializerTest(ActivitySerializationTest):
#     serialization_class = CassandraActivitySerializer
#     serialization_class_kwargs = {
#         'model': models.Activity, 'activity_class': Activity, 'aggregated_activity_class': AggregatedActivity}
