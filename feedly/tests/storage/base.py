from feedly.storage.base import BaseActivityStorage, BaseTimelineStorage
from feedly.tests.utils import FakeActivity
from feedly.tests.utils import Pin
from feedly.verbs.base import Love as PinVerb
from mock import patch
import datetime
import unittest


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.storage.__class__ in (BaseActivityStorage, BaseTimelineStorage):
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


def compare_lists(a, b):
    a_stringified = map(str, a)
    b_stringified = map(str, b)
    assert a_stringified == b_stringified


class TestBaseActivityStorageStorage(unittest.TestCase):

    '''

    Makes sure base wirings are not broken, you should
    implement this test class for every BaseActivityStorage subclass
    to make sure APIs is respected

    '''

    storage_cls = BaseActivityStorage
    storage_options = {}

    def setUp(self):
        self.pin = Pin(
            id=1, created_at=datetime.datetime.now() - datetime.timedelta(hours=1))
        self.storage = self.storage_cls(**self.storage_options)
        self.activity = FakeActivity(
            1, PinVerb, self.pin, 1, datetime.datetime.now(), {})
        self.args = ()
        self.kwargs = {}

    def tearDown(self):
        self.storage.flush()

    def test_add_to_storage(self):
        with patch.object(self.storage, 'add_to_storage') as add_to_storage:
            self.storage.add(self.activity, *self.args, **self.kwargs)
            add_to_storage.assert_called()

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
    def test_add_get(self):
        self.storage.add(self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result == self.activity

    @implementation
    def test_add_twice(self):
        self.storage.add(
            self.activity, *self.args, **self.kwargs)
        # this shouldnt raise errors
        self.storage.add(
            self.activity, *self.args, **self.kwargs)

    @implementation
    def test_get_missing(self):
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result is None

    @implementation
    def test_remove(self):
        self.storage.remove(self.activity, *self.args, **self.kwargs)

    @implementation
    def test_add_remove(self):
        self.storage.add(self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result == self.activity
        self.storage.remove(
            self.activity, *self.args, **self.kwargs)
        result = self.storage.get(
            self.activity.serialization_id, *self.args, **self.kwargs)
        assert result is None


class TestBaseTimelineStorageClass(unittest.TestCase):

    storage_cls = BaseTimelineStorage
    storage_options = {}

    def setUp(self):
        self.storage = self.storage_cls(**self.storage_options)
        self.test_key = 'key'
        if self.__class__ != TestBaseTimelineStorageClass:
            self.storage.delete(self.test_key)
        self.storage.flush()

    def tearDown(self):
        if self.__class__ != TestBaseTimelineStorageClass:
            self.storage.delete(self.test_key)
        self.storage.flush()

    @implementation
    def test_count_empty(self):
        assert self.storage.count(self.test_key) == 0

    @implementation
    def test_count_insert(self):
        assert self.storage.count(self.test_key) == 0
        self.storage.add(self.test_key, 1)
        assert self.storage.count(self.test_key) == 1

    @implementation
    def test_add_many(self):
        results = self.storage.get_slice(self.test_key, 0, None)
        # make sure no data polution
        assert results == []
        ids = range(3)
        self.storage.add_many(self.test_key, ids)
        results = self.storage.get_slice(self.test_key, 0, None)
        compare_lists(results, [2, 1, 0])

    @implementation
    def test_add_many_unique(self):
        ids = range(3) + range(3)
        self.storage.add_many(self.test_key, ids)
        results = self.storage.get_slice(self.test_key, 0, None)
        compare_lists(results, [2, 1, 0])

    @implementation
    def test_contains(self):
        ids = range(3)
        self.storage.add_many(self.test_key, ids)
        results = self.storage.get_slice(self.test_key, 0, None)
        if self.storage.contains:
            compare_lists(results, [2, 1, 0])
            present = {}
            for i in range(4):
                present[i] = self.storage.contains(self.test_key, i)
            assert present == {0: True, 1: True, 2: True, 3: False}

    @implementation
    def test_index_of(self):
        ids = range(1, 42)
        self.storage.add_many(self.test_key, ids)
        assert self.storage.index_of(self.test_key, 41) == 0
        assert self.storage.index_of(self.test_key, 7) == 34
        with self.assertRaises(ValueError):
            self.storage.index_of(self.test_key, 0)

    @implementation
    def test_trim(self):
        self.storage.add_many(self.test_key, range(10))
        assert self.storage.count(self.test_key) == 10
        self.storage.trim(self.test_key, 5)
        assert self.storage.count(self.test_key) == 5

    @implementation
    def test_remove_missing(self):
        self.storage.remove(self.test_key, 1)
        self.storage.remove_many(self.test_key, [1])

    @implementation
    def test_add_remove(self):
        assert self.storage.count(self.test_key) == 0
        self.storage.add_many(self.test_key, range(10))
        self.storage.remove_many(self.test_key, range(5, 11))
        results = self.storage.get_slice(self.test_key, 0, 20)
        assert map(str, results) == ['4', '3', '2', '1', '0']
        assert self.storage.count(self.test_key) == 5

    @implementation
    def test_get_many_empty(self):
        assert self.storage.get_slice(self.test_key, 0, 10) == []

    @implementation
    def test_timeline_order(self):
        self.storage.add_many(self.test_key, range(10))
        compare_lists(self.storage.get_slice(self.test_key, 0, 2), [9, 8])
        compare_lists(self.storage.get_slice(self.test_key, 5, 8), [4, 3, 2])
        self.storage.trim(self.test_key, 5)
        self.storage.add_many(self.test_key, range(10))
        self.storage.get_slice(self.test_key, 0, 5)
        self.storage.add_many(self.test_key, [42])
        self.storage.get_slice(self.test_key, 0, 1)

    @implementation
    def test_implements_batcher_as_ctx_manager(self):
        batcher = self.storage.get_batch_interface()
        hasattr(batcher, '__enter__')
        hasattr(batcher, '__exit__')

    @implementation
    def test_union_set_slice(self):
        keys = range(42, 0, -1)
        self.storage.add_many(self.test_key, keys)
        assert self.storage.count(self.test_key) == 42
        s1 = self.storage.get_slice(self.test_key, 0, 21)
        s2 = self.storage.get_slice(self.test_key, 22, 42)
        s3 = self.storage.get_slice(self.test_key, 22, 23)
        s4 = self.storage.get_slice(self.test_key, None, 23)
        s5 = self.storage.get_slice(self.test_key, None, None)
        s6 = self.storage.get_slice(self.test_key, 1, None)
        assert map(int, s1) == keys[0:21]
        assert map(int, s2) == keys[22:42]
        assert map(int, s3) == keys[22:23]
        assert map(int, s4) == keys[:23]
        assert map(int, s5) == keys[:]
        assert map(int, s6) == keys[1:]
        # check intersections
        assert len(set(s1 + s2)) == len(s1) + len(s2)
