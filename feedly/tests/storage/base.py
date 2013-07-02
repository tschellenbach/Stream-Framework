from feedly.storage.base import BaseActivityStorage
from feedly.storage.base import BaseTimelineStorage
from mock import patch
import unittest


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.storage.__class__ in (BaseActivityStorage, BaseTimelineStorage):
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test

class TestBaseActivityStorageStorage(unittest.TestCase):
    '''

    Makes sure base wirings are not broken, you should 
    implement this test class for every BaseActivityStorage subclass
    to make sure APIs is respected

    '''
    
    storage_cls = BaseActivityStorage

    def setUp(self):
        self.storage = self.storage_cls()
        self.activity_id = 1
        self.activity = 'activity'
        self.args = ()
        self.kwargs = {}

    def test_add_many(self):
        with patch.object(self.storage, 'add_many') as add_many:
            self.storage.add('key', self.activity_id, self.activity, *self.args, **self.kwargs)
            add_many.assert_called()
            add_many.assert_called_with('key', {self.activity_id: self.activity}, self.args, self.kwargs)

    def test_remove_many(self):
        with patch.object(self.storage, 'remove_many') as remove_many:
            self.storage.remove('key', self.activity_id)
            remove_many.assert_called()
            remove_many.assert_called_with('key', [self.activity_id], self.args, self.kwargs)

    def test_get_many(self):
        with patch.object(self.storage, 'get_many') as get_many:
            self.storage.get('key', self.activity_id)
            get_many.assert_called()
            get_many.assert_called_with('key', [self.activity_id], self.args, self.kwargs)

    @implementation
    def test_add(self):
        add_count = self.storage.add('key', self.activity_id, self.activity, *self.args, **self.kwargs)
        self.assertEqual(add_count, 1)

    @implementation
    def test_update(self):
        add_count = self.storage.add('key', self.activity_id, self.activity, *self.args, **self.kwargs)
        add_count = self.storage.add('key', self.activity_id, self.activity, *self.args, **self.kwargs)
        self.assertEqual(add_count, 0)

    @implementation
    def test_get_missing(self):
        get_ret = self.storage.get('key', self.activity_id, *self.args, **self.kwargs)
        assert get_ret is None
        assert get_ret == self.activity

    @implementation
    def test_remove(self):
        self.storage.remove('key', self.activity_id, *self.args, **self.kwargs)


class TestBaseFeedClass(unittest.TestCase):

    def test_slice_more_than(self):
        pass

    def test_slice_between(self):
        pass

    def test_slice_less_than(self):
        pass
