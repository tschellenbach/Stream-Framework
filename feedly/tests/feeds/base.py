from contextlib import nested
import datetime
from feedly.feeds.base import BaseFeed
from feedly.tests.utils import FakeActivity
from feedly.tests.utils import Pin
from feedly.verbs.base import Love as LoveVerb
from mock import patch
import unittest
import time


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.feed_cls == BaseFeed:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class TestBaseFeed(unittest.TestCase):
    feed_cls = BaseFeed

    def setUp(self):
        self.user_id = 42
        self.test_feed = self.feed_cls(self.user_id)
        self.pin = Pin(
            id=1, created_at=datetime.datetime.now() - datetime.timedelta(hours=1))
        self.activity = FakeActivity(
            1, LoveVerb, self.pin, 1, datetime.datetime.now(), {})
        activities = []
        for x in range(10):
            activity_time = datetime.datetime.now() + datetime.timedelta(
                hours=1)
            activity = FakeActivity(
                x, LoveVerb, self.pin, x, activity_time, dict(x=x))
            activities.append(activity)
        self.activities = activities

    def tearDown(self):
        if self.feed_cls != BaseFeed:
            self.test_feed.activity_storage.flush()
            self.test_feed.delete()

    def test_format_key(self):
        assert self.test_feed.key == 'feed_42'

    def test_delegate_add_many_to_storage(self):
        with nested(
                patch.object(self.test_feed.timeline_storage, 'add_many'),
                patch.object(self.test_feed.timeline_storage, 'trim')
        ) as (add_many, trim):
            self.test_feed.add(self.activity.serialization_id)
            add_many.assertCalled()
            trim.assertCalled()

    def test_delegate_count_to_storage(self):
        with patch.object(self.test_feed.timeline_storage, 'count') as count:
            self.test_feed.count()
            count.assertCalled()
            count.assert_called_with(self.test_feed.key)

    def test_delegate_delete_to_storage(self):
        with patch.object(self.test_feed.timeline_storage, 'delete') as delete:
            self.test_feed.delete()
            delete.assertCalled()
            delete.assert_called_with(self.test_feed.key)

    def test_delegate_remove_many_to_storage(self):
        with patch.object(self.test_feed.timeline_storage, 'remove_many') as remove_many:
            self.test_feed.remove(self.activity.serialization_id)
            remove_many.assertCalled()

    def test_delegate_add_to_add_many(self):
        with patch.object(self.test_feed, 'add_many') as add_many:
            self.test_feed.add(self.activity.serialization_id)
            add_many.assertCalled()

    def test_delegate_remove_to_remove_many(self):
        with patch.object(self.test_feed, 'remove_many') as remove_many:
            self.test_feed.remove(self.activity.serialization_id)
            remove_many.assertCalled()

    def test_slicing_left(self):
        with patch.object(self.test_feed, 'get_activity_slice') as get_activity_slice:
            self.test_feed[5:]
            get_activity_slice.assert_called_with(5, None)

    def test_slicing_between(self):
        with patch.object(self.test_feed, 'get_activity_slice') as get_activity_slice:
            self.test_feed[5:10]
            get_activity_slice.assert_called_with(5, 10)

    def test_slicing_right(self):
        with patch.object(self.test_feed, 'get_activity_slice') as get_activity_slice:
            self.test_feed[:5]
            get_activity_slice.assert_called_with(0, 5)

    def test_get_index(self):
        with patch.object(self.test_feed, 'get_activity_slice') as get_activity_slice:
            self.test_feed[5]
            get_activity_slice.assert_called_with(5, 6)

    @implementation
    def test_add_insert_activity(self):
        self.feed_cls.insert_activity(self.activity)
        activity = self.test_feed.activity_storage.get(
            self.activity.serialization_id
        )
        assert self.activity == activity

    @implementation
    def test_remove_missing_activity(self):
        self.feed_cls.remove_activity(self.activity)

    @implementation
    def test_add_remove_activity(self):
        self.feed_cls.insert_activity(
            self.activity
        )
        self.feed_cls.remove_activity(
            self.activity
        )
        activity = self.test_feed.activity_storage.get(
            self.activity.serialization_id,
        )
        assert activity is None

    @implementation
    def test_check_violation_unsliced_iter_feed(self):
        with self.assertRaises(TypeError):
            [i for i in self.test_feed]

    @implementation
    def test_delete(self):
        # flush is not implemented by all backends
        assert self.test_feed.count() == 0
        self.feed_cls.insert_activity(
            self.activity
        )
        self.test_feed.add(self.activity)
        assert self.test_feed.count() == 1
        assert [self.activity] == self.test_feed[0]
        self.test_feed.delete()
        assert self.test_feed.count() == 0

    @implementation
    def test_add_to_timeline(self):
        assert self.test_feed.count() == 0
        self.feed_cls.insert_activity(
            self.activity
        )
        self.test_feed.add(self.activity)
        assert [self.activity] == self.test_feed[0]
        assert self.test_feed.count() == 1

    @implementation
    def test_add_many_to_timeline(self):
        assert self.test_feed.count() == 0
        self.feed_cls.insert_activity(
            self.activity
        )
        self.test_feed.add_many([self.activity])
        assert self.test_feed.count() == 1
        assert [self.activity] == self.test_feed[0]

    @implementation
    def test_add_many_and_trim(self):
        activities = []
        for i in range(50):
            activity = FakeActivity(
                i, LoveVerb, i, i, datetime.datetime.now(), {})
            activities.append(activity)

        self.test_feed.insert_activities(activities)
        self.test_feed.add_many(activities)
        self.assertEqual(self.test_feed.count(), 50)
        self.test_feed.trim(10)
        self.assertEqual(self.test_feed.count(), 10)

    def _check_order(self, activities):
        serialization_id = [a.serialization_id for a in activities]
        assert serialization_id == sorted(serialization_id, reverse=True)
        assert activities == sorted(
            activities, key=lambda a: a.time, reverse=True)

    @implementation
    def test_feed_timestamp_order(self):
        activities = []
        deltas = [1, 2, 9, 8, 11, 10, 5, 16, 14, 50]
        for i in range(10):
            activity = FakeActivity(
                i, LoveVerb, i, i, time=datetime.datetime.now() - datetime.timedelta(seconds=deltas.pop()))
            activities.append(activity)
            self.feed_cls.insert_activity(
                activity
            )
        self.test_feed.add_many(activities)
        self._check_order(self.test_feed[:10])
        self._check_order(self.test_feed[1:9])
        self._check_order(self.test_feed[5:])

    @implementation
    def test_feed_indexof_large(self):
        assert self.test_feed.count() == 0
        activity_dict = {}
        for i in range(150):
            moment = datetime.datetime.now() - datetime.timedelta(seconds=i)
            activity = FakeActivity(i, LoveVerb, i, i, time=moment)
            activity_dict[i] = activity
        self.test_feed.insert_activities(activity_dict.values())
        self.test_feed.add_many(activity_dict.values())

        # give cassandra a moment
        time.sleep(0.1)

        activity = activity_dict[110]
        index_of = self.test_feed.index_of(activity.serialization_id)
        self.assertEqual(index_of, 110)

    @implementation
    def test_feed_slice(self):
        activity_dict = {}
        for i in range(10):
            activity = FakeActivity(
                i, LoveVerb, i, i, time=datetime.datetime.now() - datetime.timedelta(seconds=i))
            activity_dict[i] = activity
        self.test_feed.insert_activities(activity_dict.values())
        self.test_feed.add_many(activity_dict.values())

        results = self.test_feed[:]
        self.assertEqual(len(results), self.test_feed.count())

    def prepare_filter(self):
        if not self.test_feed.filtering_supported:
            return

        # setup the data
        activity_dict = {}
        for i in range(10):
            activity = FakeActivity(
                i, LoveVerb, i, i, time=datetime.datetime.now() - datetime.timedelta(seconds=i))
            activity_dict[i] = activity
        self.test_feed.insert_activities(activity_dict.values())
        self.test_feed.add_many(activity_dict.values())

    @implementation
    def test_feed_filter_copy(self):
        '''
        The feed should get deepcopied, so this method of filtering shouldnt
        work
        '''
        activity_dict = self.prepare_filter()
        if not activity_dict:
            return
        # and filter
        feed = self.test_feed
        feed.filter(activity_id__lte=activity_dict[6].serialization_id)
        results = feed.get_activity_slice(0, 2)
        self.assertEqual(len(results), 2)
        correct_results = [activity_dict[0], activity_dict[1]]
        self.assertEqual(results, correct_results)

    @implementation
    def test_feed_filter_gte(self):
        activity_dict = self.prepare_filter()
        if not activity_dict:
            return
        # and filter
        feed = self.test_feed
        feed = feed.filter(activity_id__gte=activity_dict[2].serialization_id)
        results = feed.get_activity_slice(0, 5)
        print results
        self.assertEqual(len(results), 2)
        correct_results = [activity_dict[0], activity_dict[1]]
        self.assertEqual(results, correct_results)

    @implementation
    def test_feed_filter_lte(self):
        activity_dict = self.prepare_filter()
        if not activity_dict:
            return
        # and filter
        feed = self.test_feed
        feed = feed.filter(activity_id__lte=activity_dict[6].serialization_id)
        results = feed.get_activity_slice(0, 2)
        self.assertEqual(len(results), 2)
        correct_results = [activity_dict[6], activity_dict[7]]
        self.assertEqual(results, correct_results)
