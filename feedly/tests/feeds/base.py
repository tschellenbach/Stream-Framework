import unittest
from contextlib import nested
from feedly.feeds.base import BaseFeed
from mock import patch


class FakeActivity(object):
    serialization_id = 1


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
        self.test_feed = self.feed_cls(self.user_id, {}, {})
        self.activity = FakeActivity()

    def tearDown(self):
        if self.feed_cls != BaseFeed:
            self.test_feed.activity_storage.flush()
            self.test_feed.delete()

    def test_format_key(self):
        assert self.test_feed.key == self.test_feed.key_format % self.user_id

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
        with patch.object(self.test_feed, 'get_results') as get_results:
            self.test_feed[5:]
            get_results.assert_called_with(5, None)

    def test_slicing_between(self):
        with patch.object(self.test_feed, 'get_results') as get_results:
            self.test_feed[5:10]
            get_results.assert_called_with(5, 10)

    def test_slicing_right(self):
        with patch.object(self.test_feed, 'get_results') as get_results:
            self.test_feed[:5]
            get_results.assert_called_with(0, 5)

    def test_get_index(self):
        with patch.object(self.test_feed, 'get_results') as get_results:
            self.test_feed[5]
            get_results.assert_called_with(5, 6)

    @implementation
    def test_add_insert_activity(self):
        self.feed_cls.insert_activity(self.activity)
        activity = self.test_feed.activity_storage.get(
            self.activity.serialization_id
        )
        assert self.activity == activity

    @implementation
    def test_remove_missing_activity(self):
        self.test_feed.remove_activity(self.activity)

    @implementation
    def test_add_remove_activity(self):
        self.test_feed.insert_activity(self.activity)
        self.test_feed.activity_storage.get(
            self.activity.serialization_id
        )
        self.test_feed.remove_activity(self.activity)
        activity = self.test_feed.activity_storage.get(
            self.activity.serialization_id
        )
        assert activity == None

    @implementation
    def test_check_violation_unsliced_iter_feed(self):
        with self.assertRaises(TypeError):
            [i for i in self.test_feed]

    @implementation
    def test_add_to_timeline(self):
        assert self.test_feed.count() == 0
        self.test_feed.insert_activity(self.activity)
        self.test_feed.add(self.activity.serialization_id)
        assert [self.activity] == self.test_feed[0]
        assert self.test_feed.count() == 1

    @implementation
    def test_add_many_to_timeline(self):
        assert self.test_feed.count() == 0
        self.test_feed.insert_activity(self.activity)
        self.test_feed.add_many([self.activity.serialization_id])
        assert self.test_feed.count() == 1
        assert [self.activity] == self.test_feed[0]


