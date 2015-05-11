from stream_framework.storage.base_lists_storage import BaseListsStorage

import unittest


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.lists_storage_class == BaseListsStorage:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class TestBaseListsStorage(unittest.TestCase):

    lists_storage_class = BaseListsStorage
    key = 'test'
    max_length = 100

    def setUp(self):
        self.lists_storage = self.lists_storage_class(key=self.key,
                                                      max_length = self.max_length)

    def tearDown(self):
        if self.lists_storage_class != BaseListsStorage:
            self.lists_storage.flush('whenever', 'everyday', 'whatever')

    @implementation
    def test_add_empty_values(self):
        self.lists_storage.add(whenever=[])
        count = self.lists_storage.count('whenever')
        self.assertEqual(count, 0)

        self.lists_storage.add(whenever=[1, 2], everyday=[])
        count = self.lists_storage.count('whenever')
        self.assertEqual(count, 2)
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 0)

    @implementation
    def test_add_more_than_allowed(self):
        items = list(range(0, self.max_length + 1))
        self.lists_storage.add(whatever=items)
        stored_items = self.lists_storage.get('whatever')
        self.assertEqual(items[1:], stored_items)

    @implementation
    def test_add(self):
        self.lists_storage.add(whenever=[1])
        count = self.lists_storage.count('whenever')
        self.assertEqual(count, 1)

        self.lists_storage.add(everyday=[1, 2])
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 2)

        self.lists_storage.add(whenever=[3], everyday=[3, 4])
        count = self.lists_storage.count('whenever')
        self.assertEqual(count, 2)
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 4)

    @implementation
    def test_count_not_exisit_list(self):
        count = self.lists_storage.count('whatever')
        self.assertEqual(count, 0)

    @implementation
    def test_get_from_not_exisiting_list(self):
        items = self.lists_storage.get('whenever')
        self.assertEqual([], items)

        self.lists_storage.add(everyday=[1,2])
        whenever_items, _ = self.lists_storage.get('whenever', 'everyday')
        self.assertEqual([], whenever_items)

    @implementation
    def test_get(self):
        whenever_items = list(range(0, 20))
        everyday_items = list(range(10, 0, -1))
        self.lists_storage.add(whenever=whenever_items, everyday=everyday_items)

        stored_items = self.lists_storage.get('whenever')
        self.assertEqual(stored_items, whenever_items)

        stored_items = self.lists_storage.get('everyday')
        self.assertEqual(stored_items, everyday_items)

        stored_whenever_items, stored_everyday_items = self.lists_storage.get('whenever', 'everyday')
        self.assertEqual(stored_whenever_items, whenever_items)
        self.assertEqual(stored_everyday_items, everyday_items)

    @implementation
    def test_remove_not_existing_items(self):
        items = [1,2,3]
        self.lists_storage.add(whenever=items)

        self.lists_storage.remove(whenever=[0])
        stored_items = self.lists_storage.get('whenever')
        self.assertEqual(stored_items, items)

        self.lists_storage.remove(whenever=[0,2])
        stored_items = self.lists_storage.get('whenever')
        self.assertEqual(stored_items, [1,3])

    @implementation
    def test_remove_from_not_exisiting_list(self):
        self.lists_storage.remove(whenever=[1,2])

        self.lists_storage.add(everyday=[1,2])
        self.lists_storage.remove(whenever=[1,2])
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 2)

    @implementation
    def test_remove(self):
        whenever_items = list(range(0, 20))
        everyday_items = list(range(10, 0, -1))
        self.lists_storage.add(whenever=whenever_items, everyday=everyday_items)

        self.lists_storage.remove(whenever=[15])
        whenever_items.remove(15)
        stored_items = self.lists_storage.get('whenever')
        self.assertEqual(stored_items, whenever_items)

        self.lists_storage.remove(everyday=[1, 5])
        everyday_items.remove(1)
        everyday_items.remove(5)
        stored_items = self.lists_storage.get('everyday')
        self.assertEqual(stored_items, everyday_items)

        self.lists_storage.remove(whenever=[5, 19], everyday=[2])
        whenever_items.remove(5)
        whenever_items.remove(19)
        everyday_items.remove(2)
        stored_whenever_items, stored_everyday_items = self.lists_storage.get('whenever', 'everyday')
        self.assertEqual(stored_whenever_items, whenever_items)
        self.assertEqual(stored_everyday_items, everyday_items)

    @implementation
    def test_flush_non_existing_list(self):
        self.lists_storage.flush('whenever')

        self.lists_storage.add(everyday=[1,2])
        self.lists_storage.flush('whenever')
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 2)

    @implementation
    def test_flush_already_flushed_list(self):
        self.lists_storage.add(everyday=[1,2])
        self.lists_storage.flush('everyday')

        self.lists_storage.flush('everyday')
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 0)

    @implementation
    def test_flush(self):
        whenever_items = list(range(0, 20))
        everyday_items = list(range(10, 0, -1))
        self.lists_storage.add(whenever=whenever_items, everyday=everyday_items)

        self.lists_storage.flush('whenever')
        count = self.lists_storage.count('whenever')
        self.assertEqual(count, 0)

        self.lists_storage.flush('everyday')
        count = self.lists_storage.count('everyday')
        self.assertEqual(count, 0)

        self.lists_storage.add(whenever=whenever_items, everyday=everyday_items)
        self.lists_storage.flush('whenever', 'everyday')
        whenever_count, everyday_count = self.lists_storage.count('whenever', 'everyday')
        self.assertEqual(whenever_count, 0)
        self.assertEqual(everyday_count, 0)

    @implementation
    def test_keep_max_length(self):
        items = list(range(0, self.max_length))
        self.lists_storage.add(whenever=items)
        self.lists_storage.add(whenever=[self.max_length])

        count = self.lists_storage.count('whenever')
        self.assertEqual(count, self.max_length)

        items.remove(0)
        items.append(self.max_length)

        stored_items = self.lists_storage.get('whenever')
        self.assertEqual(items, stored_items)
