from feedly.activity import Activity
from feedly.tests.utils import Pin
from feedly.verbs.base import Love as LoveVerb
import unittest


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
        Verb = type('Overflow', (LoveVerb, ), {'id': 9999})
        activity = Activity(1, Verb, activity_object)
        with self.assertRaises(TypeError):
            activity.serialization_id
