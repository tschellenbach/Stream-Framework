import unittest
from feedly.storage.redis.structures.hash import RedisHashCache,\
    ShardedHashCache, FallbackHashCache
from feedly.storage.redis.structures.list import RedisListCache,\
    FallbackRedisListCache
from feedly.storage.redis.connection import get_redis_connection
from functools import partial
from feedly.storage.redis.structures.sorted_set import RedisSortedSetCache


class BaseRedisStructureTestCase(unittest.TestCase):

    def get_structure(self):
        return


class RedisSortedSetTest(BaseRedisStructureTestCase):

    test_data = [(1.0, 'a'), (2.0, 'b'), (3.0, 'c')]

    def get_structure(self):
        structure_class = RedisSortedSetCache
        structure = structure_class('test')
        structure.delete()
        return structure

    def test_add_many(self):
        cache = self.get_structure()
        test_data = self.test_data
        for key, value in test_data:
            cache.add(key, value)
        # this shouldnt insert data, its a sorted set after all
        cache.add_many(test_data)
        count = cache.count()
        self.assertEqual(int(count), 3)

    def test_ordering(self):
        cache = self.get_structure()
        data = self.test_data

        test_data = data
        cache.add_many(test_data)
        results = cache[:]
        expected_results = [p[::-1] for p in test_data]
        self.assertEqual(results, expected_results[::-1])
        cache.sort_asc = True
        results = cache[:10]
        self.assertEqual(results, expected_results)

    def test_trim(self):
        cache = self.get_structure()
        test_data = self.test_data
        for score, value in test_data:
            cache.add(score, value)
        cache.trim(1)
        count = cache.count()
        self.assertEqual(count, 1)

    def test_simple_trim(self):
        cache = self.get_structure()
        test_data = self.test_data
        for key, value in test_data:
            cache.add(key, value)
        cache.max_length = 1
        cache.trim()
        count = int(cache.count())
        self.assertEqual(count, 1)

    def test_remove(self):
        cache = self.get_structure()
        test_data = self.test_data
        cache.add_many(test_data)
        cache.remove_many(['a'])
        count = cache.count()
        self.assertEqual(count, 2)

    def test_remove_by_score(self):
        cache = self.get_structure()
        test_data = self.test_data
        cache.add_many(test_data)
        cache.remove_by_scores([1.0, 2.0])
        count = cache.count()
        self.assertEqual(count, 1)

    def test_zremrangebyrank(self):
        redis = get_redis_connection()
        key = 'test'
        # start out fresh
        redis.delete(key)
        redis.zadd(key, 1, 'a')
        redis.zadd(key, 2, 'b')
        redis.zadd(key, 3, 'c')
        redis.zadd(key, 4, 'd')
        redis.zadd(key, 5, 'e')
        expected_results = [('a', 1.0), ('b', 2.0), ('c', 3.0), (
            'd', 4.0), ('e', 5.0)]
        results = redis.zrange(key, 0, -1, withscores=True)
        self.assertEqual(results, expected_results)
        results = redis.zrange(key, 0, -4, withscores=True)

        # now the idea is to only keep 3,4,5
        max_length = 3
        end = (max_length * -1) - 1
        redis.zremrangebyrank(key, 0, end)
        expected_results = [('c', 3.0), ('d', 4.0), ('e', 5.0)]
        results = redis.zrange(key, 0, -1, withscores=True)
        self.assertEqual(results, expected_results)


class ListCacheTestCase(BaseRedisStructureTestCase):

    def get_structure(self):
        structure_class = type(
            'MyCache', (RedisListCache, ), dict(max_items=10))
        structure = structure_class('test')
        structure.delete()
        return structure

    def test_append(self):
        cache = self.get_structure()
        cache.append_many(['a', 'b'])
        self.assertEqual(cache[:5], ['a', 'b'])
        self.assertEqual(cache.count(), 2)

    def test_simple_append(self):
        cache = self.get_structure()
        for value in ['a', 'b']:
            cache.append(value)
        self.assertEqual(cache[:5], ['a', 'b'])
        self.assertEqual(cache.count(), 2)

    def test_trim(self):
        cache = self.get_structure()
        cache.append_many(range(100))
        self.assertEqual(cache.count(), 100)
        cache.trim()
        self.assertEqual(cache.count(), 10)

    def test_remove(self):
        cache = self.get_structure()
        data = ['a', 'b']
        cache.append_many(data)
        self.assertEqual(cache[:5], data)
        self.assertEqual(cache.count(), 2)
        for value in data:
            cache.remove(value)
        self.assertEqual(cache[:5], [])
        self.assertEqual(cache.count(), 0)


class FakeFallBack(FallbackRedisListCache):
    max_items = 10

    def __init__(self, *args, **kwargs):
        self.fallback_data = kwargs.pop('fallback')
        FallbackRedisListCache.__init__(self, *args, **kwargs)

    def get_fallback_results(self, start, stop):
        return self.fallback_data[start:stop]


class FallbackRedisListCacheTest(ListCacheTestCase):

    def get_structure(self):
        structure = FakeFallBack('test', fallback=['a', 'b'])
        structure.delete()
        return structure

    def test_remove(self):
        cache = self.get_structure()
        data = ['a', 'b']
        cache.append_many(data)
        self.assertEqual(cache[:5], data)
        self.assertEqual(cache.count(), 2)
        for value in data:
            cache.remove(value)
        self.assertEqual(cache.count(), 0)
        # fallback should still work
        self.assertEqual(cache[:5], data)


class SecondFallbackRedisListCacheTest(BaseRedisStructureTestCase):

    def get_structure(self):
        structure = FakeFallBack('test', fallback=['a', 'b', 'c'])
        structure.delete()
        return structure

    def test_append(self):
        cache = self.get_structure()
        # test while we have no redis data
        self.assertEqual(cache[:5], ['a', 'b', 'c'])
        # now test with redis data
        cache.append_many(['d', 'e', 'f', 'g'])
        self.assertEqual(cache.count(), 7)
        self.assertEqual(cache[:3], ['a', 'b', 'c'])

    def test_slice(self):
        cache = self.get_structure()
        # test while we have no redis data
        self.assertEqual(cache[:], ['a', 'b', 'c'])


class HashCacheTestCase(BaseRedisStructureTestCase):

    def get_structure(self):
        structure = RedisHashCache('test')
        # always start fresh
        structure.delete()
        return structure

    def test_set_many(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        keys = cache.keys()
        self.assertEqual(keys, ['key', 'key2'])

    def test_set(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        for key, value in key_value_pairs:
            cache.set(key, value)
        keys = cache.keys()
        self.assertEqual(keys, ['key', 'key2'])

    def test_delete_many(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        keys = cache.keys()
        cache.delete_many(keys)
        keys = cache.keys()
        self.assertEqual(keys, [])

    def test_get_and_set(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        results = cache.get_many(['key', 'key2'])
        self.assertEqual(results, {'key2': 'value2', 'key': 'value'})

        result = cache.get('key')
        self.assertEqual(result, 'value')

        result = cache.get('key_missing')
        self.assertEqual(result, None)

    def test_contains(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        result = cache.contains('key')
        self.assertEqual(result, True)
        result = cache.contains('key2')
        self.assertEqual(result, True)
        result = cache.contains('key_missing')
        self.assertEqual(result, False)

    def test_count(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        count = cache.count()
        self.assertEqual(count, 2)


class MyFallbackHashCache(FallbackHashCache):

    def get_many_from_fallback(self, fields):
        return dict(zip(fields, range(100)))


class FallbackHashCacheTestCase(HashCacheTestCase):

    def get_structure(self):
        structure = MyFallbackHashCache('test')
        # always start fresh
        structure.delete()
        return structure

    def test_get_and_set(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        results = cache.get_many(['key', 'key2'])
        self.assertEqual(results, {'key2': 'value2', 'key': 'value'})

        result = cache.get('key')
        self.assertEqual(result, 'value')

        result = cache.get('key_missing')
        self.assertEqual(result, 0)


class ShardedHashCacheTestCase(HashCacheTestCase):

    def get_structure(self):
        structure = ShardedHashCache('test')
        # always start fresh
        structure.delete()
        return structure

    def test_set_many(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)

    def test_get_and_set(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        results = cache.get_many(['key', 'key2'])
        self.assertEqual(results, {'key2': 'value2', 'key': 'value'})

        result = cache.get('key')
        self.assertEqual(result, 'value')

        result = cache.get('key_missing')
        self.assertEqual(result, None)

    def test_count(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        count = cache.count()
        self.assertEqual(count, 2)

    def test_contains(self):
        cache = self.get_structure()
        key_value_pairs = [('key', 'value'), ('key2', 'value2')]
        cache.set_many(key_value_pairs)
        contains = partial(cache.contains, 'key')
        self.assertRaises(NotImplementedError, contains)
