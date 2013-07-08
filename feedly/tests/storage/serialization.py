from feedly.storage.utils.serializers.activity_serializer import \
    ActivitySerializer
from feedly.storage.utils.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
from feedly.storage.utils.serializers.base import BaseSerializer
from feedly.storage.utils.serializers.love_activity_serializer import \
    LoveActivitySerializer
from feedly.storage.utils.serializers.pickle_serializer import PickleSerializer
from feedly.tests.utils import FakeActivity, FakeAggregatedActivity
import datetime
import unittest


class SerializationTestCase(unittest.TestCase):
    serialization_cls = BaseSerializer
    
    def setUp(self):
        from feedly.verbs.base import Love as LoveVerb
        self.serializer = self.serialization_cls()
        self.activity = FakeActivity(1, LoveVerb, 1, 1, datetime.datetime.now(), {})
        self.args = ()
        self.kwargs = {}

    def test_serialization(self):
        serialized_activity = self.serializer.dumps(self.activity)
        deserialized_activity = self.serializer.loads(serialized_activity)
        self.assertEqual(deserialized_activity, self.activity)


class PickleSerializationTestCase(SerializationTestCase):
    serialization_cls = PickleSerializer


class ActivitySerializerTest(SerializationTestCase):
    serialization_cls = ActivitySerializer


class AggregatedActivitySerializerTest(SerializationTestCase):
    serialization_cls = AggregatedActivitySerializer
    
    def setUp(self):
        SerializationTestCase.setUp(self)
        activities = [self.activity]
        fake_aggregated_activity = FakeAggregatedActivity('group', activities)
        self.activity = fake_aggregated_activity


class LoveActivitySerializerTest(SerializationTestCase):
    serialization_cls = LoveActivitySerializer