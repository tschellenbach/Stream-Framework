import unittest
from stream_framework.storage.redis.structures.hash import RedisHashCache, \
    ShardedHashCache, FallbackHashCache
from stream_framework.storage.redis.structures.list import RedisListCache, \
    FallbackRedisListCache
from stream_framework.storage.redis.connection import get_redis_connection
from functools import partial
from stream_framework.storage.redis.structures.sorted_set import RedisSortedSetCache


class BaseRedisStructureTestCase(unittest.TestCase):

    def get_structure(self):
        return


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.__class__ == BaseRedisSortedSetTest:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class BaseRedisSortedSetTest(BaseRedisStructureTestCase):

    test_data = [(3.0, 'a'), (2.0, 'b'), (1.0, 'c')]
    asc_sorted = False

    @property
    def test_results(self):
        return [p[::-1] for p in self.test_data]

    @property
    def test_scores(self):
        return [p[0] for p in self.test_data]

    def get_structure(self):
        structure_class = RedisSortedSetCache
        structure = structure_class('test')
        structure.delete()
        structure.sort_asc = self.asc_sorted
        return structure

    @implementation
    def test_add_many(self):
        cache = self.get_structure()
        test_data = self.test_data
        for key, value in test_data:
            cache.add(key, value)
        # this shouldnt insert data, its a sorted set after all
        cache.add_many(test_data)
        count = cache.count()
        self.assertEqual(int(count), 3)
        results = cache[:]
        self.assertEqual(results, self.test_results[:])

    @implementation
    def test_ordering(self):
        cache = self.get_structure()
        cache.add_many(self.test_data)
        results = cache[:]
        self.assertEqual(results, self.test_results[:])

    @implementation
    def test_filtering(self):
        # setup the data
        cache = self.get_structure()
        cache.add_many(self.test_data)

        # try a max
        results = cache.get_results(0, 2, max_score=self.test_scores[1])
        if self.asc_sorted:
            self.assertEqual(results, self.test_results[0:2])
        else:
            self.assertEqual(results, self.test_results[1:])

        # try a min
        results = cache.get_results(0, 2, min_score=self.test_scores[1])
        if self.asc_sorted:
            self.assertEqual(results, self.test_results[1:])
        else:
            self.assertEqual(results, self.test_results[0:2])

        # try a max with a start
        results = cache.get_results(1, 2, max_score=self.test_scores[1])
        if self.asc_sorted:
            self.assertEqual(results, self.test_results[1:2])
        else:
            self.assertEqual(results, self.test_results[2:])

    def test_long_filtering(self):
        '''
        Check if nothing breaks when using long numbers as scores
        '''
        self.skipTest('This is a known issue with Redis')
        # setup the data
        test_data = [(13930920300000000000007001, 'a'), (
            13930920300000000000007002, 'b'), (13930920300000000000007003, 'c')]
        cache = self.get_structure()
        cache.add_many(test_data)
        # try a max
        results = cache.get_results(0, 2, max_score=13930920300000000000007002)
        self.assertEqual(results, [('b', float(13930920300000000000007002)), (
            'a', float(13930920300000000000007001))])
        # try a min
        results = cache.get_results(0, 2, min_score=13930920300000000000007002)
        self.assertEqual(results, [('c', float(13930920300000000000007003)), (
            'b', float(13930920300000000000007002))])
        # try a max with a start
        results = cache.get_results(1, 2, max_score=13930920300000000000007002)
        self.assertEqual(results, [('a', float(13930920300000000000007001))])

    @implementation
    def test_trim(self):
        cache = self.get_structure()
        test_data = self.test_data
        for score, value in test_data:
            cache.add(score, value)
        cache.trim(2)
        count = cache.count()
        self.assertEqual(count, 2)
        results = cache[:]
        self.assertEqual(results, self.test_results[0:2])

    @implementation
    def test_simple_trim(self):
        cache = self.get_structure()
        test_data = self.test_data
        for key, value in test_data:
            cache.add(key, value)
        cache.max_length = 1
        cache.trim()
        count = int(cache.count())
        self.assertEqual(count, 1)
        results = cache[:]
        self.assertEqual(results, self.test_results[0:1])

    @implementation
    def test_remove(self):
        cache = self.get_structure()
        test_data = self.test_data
        cache.add_many(test_data)
        cache.remove_many(test_data[0][1])
        count = cache.count()
        self.assertEqual(count, 2)
        results = cache[:]
        self.assertEqual(results, self.test_results[1:])

    @implementation
    def test_remove_by_score(self):
        cache = self.get_structure()
        test_data = self.test_data
        cache.add_many(test_data)
        cache.remove_by_scores(self.test_scores[1:])
        count = cache.count()
        self.assertEqual(count, 1)
        results = cache[:]
        self.assertEqual(results, self.test_results[0:1])

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


class RedisDescSortedSetTest(BaseRedisSortedSetTest):
    pass

class RedisAscSortedSetTest(BaseRedisSortedSetTest):

    test_data = [(1.0, 'a'), (2.0, 'b'), (3.0, 'c')]
    asc_sorted = True


class ListCacheTestCase(BaseRedisStructureTestCase):

    def get_structure(self):
        structure_class = type(
            'MyCache', (RedisListCache,), dict(max_items=10))
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
