from stream_framework.activity import Activity
from stream_framework.storage.base import BaseActivityStorage, BaseTimelineStorage
from stream_framework.verbs.base import Love as PinVerb
from stream_framework.tests.utils import FakeActivity, Pin
from mock import patch
import datetime
import unittest
import time


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.storage.__class__ in (BaseActivityStorage, BaseTimelineStorage):
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


def compare_lists(a, b, msg):
    a_stringified = list(map(str, a))
    b_stringified = list(map(str, b))
    assert a_stringified == b_stringified, msg


class TestBaseActivityStorageStorage(unittest.TestCase):

    '''

    Makes sure base wirings are not broken, you should
    implement this test class for every BaseActivityStorage subclass
    to make sure APIs is respected

    '''

    storage_cls = BaseActivityStorage
    storage_options = {'activity_class': Activity}

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
            self.assertTrue(add_to_storage.called)

    def test_remove_from_storage(self):
        with patch.object(self.storage, 'remove_from_storage') as remove_from_storage:
            self.storage.remove(self.activity)
            remove_from_storage.assert_called_with(
                [self.activity.serialization_id], *self.args, **self.kwargs)

    def test_get_from_storage(self):
        with patch.object(self.storage, 'get_from_storage') as get_from_storage:
            self.storage.get(self.activity)
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
    storage_options = {'activity_class': Activity}

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

    def _build_activity_list(self, ids_list):
        now = datetime.datetime.now()
        pins = [Pin(id=i, created_at=now + datetime.timedelta(hours=i))
                for i in ids_list]
        pins_ids = zip(pins, ids_list)
        return [FakeActivity(i, PinVerb, pin, i, now + datetime.timedelta(hours=i), {'i': i}) for pin, i in pins_ids]

    def assert_results(self, results, activities, msg=''):
        activity_ids = []
        extra_context = []
        for result in results:
            if hasattr(result, 'serialization_id'):
                activity_ids.append(result.serialization_id)
            else:
                activity_ids.append(result)
            if hasattr(result, 'extra_context'):
                extra_context.append(result.extra_context)
        compare_lists(
            activity_ids, [a.serialization_id for a in activities], msg)

        if extra_context:
            self.assertEquals(
                [a.extra_context for a in activities], extra_context)

    @implementation
    def test_count_empty(self):
        assert self.storage.count(self.test_key) == 0

    @implementation
    def test_count_insert(self):
        assert self.storage.count(self.test_key) == 0
        activity = self._build_activity_list([1])[0]
        self.storage.add(self.test_key, activity)
        assert self.storage.count(self.test_key) == 1

    @implementation
    def test_add_many(self):
        results = self.storage.get_slice(self.test_key, 0, None)
        # make sure no data polution
        assert results == []
        activities = self._build_activity_list(range(3, 0, -1))
        self.storage.add_many(self.test_key, activities)
        results = self.storage.get_slice(self.test_key, 0, None)
        self.assert_results(results, activities)

    @implementation
    def test_add_many_unique(self):
        activities = self._build_activity_list(
            list(range(3, 0, -1)) + list(range(3, 0, -1)))
        self.storage.add_many(self.test_key, activities)
        results = self.storage.get_slice(self.test_key, 0, None)
        self.assert_results(results, activities[:3])

    @implementation
    def test_contains(self):
        activities = self._build_activity_list(range(4, 0, -1))
        self.storage.add_many(self.test_key, activities[:3])
        results = self.storage.get_slice(self.test_key, 0, None)
        if self.storage.contains:
            self.assert_results(results, activities[:3])
            for a in activities[:3]:
                assert self.storage.contains(self.test_key, a.serialization_id)
            assert not self.storage.contains(
                self.test_key, activities[3].serialization_id)

    @implementation
    def test_index_of(self):
        activities = self._build_activity_list(range(1, 43))
        activity_ids = [a.serialization_id for a in activities]
        self.storage.add_many(self.test_key, activities)
        assert self.storage.index_of(self.test_key, activity_ids[41]) == 0
        assert self.storage.index_of(self.test_key, activity_ids[7]) == 34
        with self.assertRaises(ValueError):
            self.storage.index_of(self.test_key, 0)

    @implementation
    def test_trim(self):
        activities = self._build_activity_list(range(10, 0, -1))
        for a in activities[5:] + activities[:5]:
            time.sleep(0.1)
            self.storage.add_many(self.test_key, [a])
        assert self.storage.count(self.test_key) == 10
        self.storage.trim(self.test_key, 5)
        assert self.storage.count(self.test_key) == 5
        results = self.storage.get_slice(self.test_key, 0, None)
        self.assert_results(
            results, activities[:5], 'check trim direction')

    @implementation
    def test_noop_trim(self):
        activities = self._build_activity_list(range(10, 0, -1))
        self.storage.add_many(self.test_key, activities)
        assert self.storage.count(self.test_key) == 10
        self.storage.trim(self.test_key, 12)
        assert self.storage.count(self.test_key) == 10

    @implementation
    def test_trim_empty_feed(self):
        self.storage.trim(self.test_key, 12)

    @implementation
    def test_remove_missing(self):
        activities = self._build_activity_list(range(10))
        self.storage.remove(self.test_key, activities[1])
        self.storage.remove_many(self.test_key, activities[1:2])

    @implementation
    def test_add_remove(self):
        assert self.storage.count(self.test_key) == 0
        activities = self._build_activity_list(range(10, 0, -1))
        self.storage.add_many(self.test_key, activities)
        self.storage.remove_many(self.test_key, activities[5:])
        results = self.storage.get_slice(self.test_key, 0, 20)
        assert self.storage.count(self.test_key) == 5
        self.assert_results(results, activities[:5])

    @implementation
    def test_get_many_empty(self):
        assert self.storage.get_slice(self.test_key, 0, 10) == []

    @implementation
    def test_timeline_order(self):
        activities = self._build_activity_list(range(10, 0, -1))
        self.storage.add_many(self.test_key, activities)
        self.storage.trim(self.test_key, 5)
        self.storage.add_many(self.test_key, activities)
        results = self.storage.get_slice(self.test_key, 0, 5)
        self.assert_results(results, activities[:5])

    @implementation
    def test_implements_batcher_as_ctx_manager(self):
        batcher = self.storage.get_batch_interface()
        hasattr(batcher, '__enter__')
        hasattr(batcher, '__exit__')

    @implementation
    def test_union_set_slice(self):
        activities = self._build_activity_list(range(42, 0, -1))
        self.storage.add_many(self.test_key, activities)
        assert self.storage.count(self.test_key) == 42
        s1 = self.storage.get_slice(self.test_key, 0, 21)
        self.assert_results(s1, activities[0:21])
        s2 = self.storage.get_slice(self.test_key, 22, 42)
        self.assert_results(s2, activities[22:42])
        s3 = self.storage.get_slice(self.test_key, 22, 23)
        self.assert_results(s3, activities[22:23])
        s4 = self.storage.get_slice(self.test_key, None, 23)
        self.assert_results(s4, activities[:23])
        s5 = self.storage.get_slice(self.test_key, None, None)
        self.assert_results(s5, activities[:])
        s6 = self.storage.get_slice(self.test_key, 1, None)
        self.assert_results(s6, activities[1:])
        # check intersections
        assert len(set(s1 + s2)) == len(s1) + len(s2)
