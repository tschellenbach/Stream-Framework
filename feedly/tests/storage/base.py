from feedly.storage.base import BaseActivityStorage
from feedly.storage.base import BaseTimelineStorage
from mock import patch
import unittest
from feedly.activity import Activity
import datetime
from feedly.verbs.base import Pin as PinVerb





class TestBaseActivityStorageStorage(unittest.TestCase):

    '''

    Makes sure base wirings are not broken, you should
    implement this test class for every BaseActivityStorage subclass
    to make sure APIs is respected

    '''

    storage_cls = BaseActivityStorage

    def setUp(self):
        self.storage = self.storage_cls()
        self.activity = FakeActivity(1, PinVerb, 1, 1, datetime.datetime.now(), {})
        self.args = ()
        self.kwargs = {}

    def tearDown(self):
        self.storage.flush()

    def test_add_to_storage(self):
        with patch.object(self.storage, 'add_to_storage') as add_to_storage:
            self.storage.add(self.activity, *self.args, **self.kwargs)
            add_to_storage.assert_called()
            activity_dict = self.storage.serialize_activity(self.activity)
            add_to_storage.assert_called_with(
                activity_dict, *self.args, **self.kwargs)

    def test_remove_from_storage(self):
        with patch.object(self.storage, 'remove_from_storage') as remove_from_storage:
            self.storage.remove(self.activity)
            remove_from_storage.assert_called()
            remove_from_storage.assert_called_with(
                [self.activity.serialization_id], *self.args, **self.kwargs)

    def test_get_from_storage(self):
        with patch.object(self.storage, 'get_from_storage') as get_from_storage:
            self.storage.get(self.activity)
            get_from_storage.assert_called()
            get_from_storage.assert_called_with(
                [self.activity], *self.args, **self.kwargs)

    @implementation
    def test_add(self):
        add_count = self.storage.add(
            self.activity, *self.args, **self.kwargs)
        self.assertEqual(add_count, 1)

    @implementation
    def test_add_twice(self):
        add_count = self.storage.add(
            self.activity, *self.args, **self.kwargs)
        add_count = self.storage.add(
            self.activity, *self.args, **self.kwargs)
        self.assertEqual(add_count, 0)

    @implementation
    def test_get_missing(self):
        result = self.storage.get(
            self.activity, *self.args, **self.kwargs)
        assert result is None

    @implementation
    def test_add_get_missing(self):
        self.storage.add(self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result == self.activity

    @implementation
    def test_remove(self):
        rem_count = self.storage.remove(
            self.activity, *self.args, **self.kwargs)
        assert rem_count == 0

    @implementation
    def test_add_remove(self):
        self.storage.add(self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result == self.activity
        rem_count = self.storage.remove(
            self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity, *self.args, **self.kwargs)
        assert result is None
        assert rem_count == 1


class TestBaseTimelineStorageClass(unittest.TestCase):

    storage_cls = BaseTimelineStorage

    def setUp(self):
        self.storage = self.storage_cls()
        self.test_key = 'key'

    def tearDown(self):
        if self.storage.__class__ != BaseTimelineStorage:
            self.storage.delete(self.test_key)

    @implementation
    def test_count_empty(self):
        assert self.storage.count(self.test_key) == 0

    @implementation
    def test_count_insert(self):
        assert self.storage.count(self.test_key) == 0
        self.storage.add(self.test_key, 1)
        assert self.storage.count(self.test_key) == 1

    @implementation
    def test_add_count(self):
        assert self.storage.add(self.test_key, 1) == 1

    @implementation
    def test_add_many_count(self):
        ids = range(3) + range(3)
        assert self.storage.add_many(self.test_key, ids) == 3

    @implementation
    def test_trim(self):
        self.storage.add_many(self.test_key, range(10))
        assert self.storage.count(self.test_key) == 10
        self.storage.trim(self.test_key, 5)
        assert self.storage.count(self.test_key) == 5

    @implementation
    def test_remove_missing(self):
        self.storage.remove(self.test_key, 1) == 0
        self.storage.remove_many(self.test_key, [1]) == 0

    @implementation
    def test_add_remove(self):
        self.storage.add_many(self.test_key, range(10))
        assert self.storage.remove_many(self.test_key, range(5, 11)) == 5

    @implementation
    def test_get_many_empty(self):
        assert self.storage.get_many(self.test_key, 0, 10) == []

    @implementation
    def test_timeline_order(self):
        self.storage.add_many(self.test_key, range(10))
        assert self.storage.get_many(self.test_key, 0, 2) == [9, 8]
        assert self.storage.get_many(self.test_key, 5, 8) == [4, 3, 2]
        self.storage.trim(self.test_key, 5)
        self.storage.add_many(self.test_key, range(10))
        self.storage.get_many(self.test_key, 0, 5) == [4, 3, 2, 1, 0]
        self.storage.add_many(self.test_key, [42])
        self.storage.get_many(self.test_key, 0, 1) == [42]
