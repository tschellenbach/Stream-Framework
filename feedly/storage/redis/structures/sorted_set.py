from django.utils.functional import lazy
from feedly.storage.redis.structures.hash import BaseRedisHashCache
from feedly.storage.redis.structures.list import BaseRedisListCache
import logging
from feedly.utils import epoch_to_datetime, chunks
logger = logging.getLogger(__name__)


class RedisSortedSetCache(BaseRedisListCache, BaseRedisHashCache):
    sort_asc = False

    def count(self):
        '''
        Returns the number of elements in the sorted set
        '''
        key = self.get_key()
        redis_result = self.redis.zcount(key, '-inf', '+inf')
        # lazily convert this to an int, this keeps it compatible with
        # distributed connections
        redis_count = lambda: int(redis_result)
        lazy_factory = lazy(redis_count, int, long)
        lazy_object = lazy_factory()
        return lazy_object

    def index_of(self, value):
        key = self.get_key()
        result = self.redis.zrevrank(key, value)
        if result:
            result = int(result)
        elif result is None:
            raise ValueError(
                'Couldnt find item with value %s in key %s' % (value, key))
        return result

    def add(self, score, key):
        score_value_pairs = [(score, key)]
        results = self.add_many(score_value_pairs)
        result = results[0]
        return result

    def add_many(self, score_value_pairs):
        '''
        StrictRedis so it expects score1, name1
        '''
        key = self.get_key()
        scores = [score for score, value in score_value_pairs]
        msg_format = 'please send floats as the first part of the pairs got %s'
        numeric_types = (float, int, long)
        if not all([isinstance(score, numeric_types) for score in scores]):
            raise ValueError(msg_format % score_value_pairs)
        results = []

        def _add_many(redis, score_value_pairs):
            score_value_list = sum(map(list, score_value_pairs), [])
            score_value_chunks = chunks(score_value_list, 200)

            for score_value_chunk in score_value_chunks:
                result = redis.zadd(key, *score_value_chunk)
                logger.debug('adding to %s with score_value_chunk %s',
                             key, score_value_chunk)
                results.append(result)
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_add_many, score_value_pairs)

        return results

    def remove_many(self, values):
        '''
        values
        '''
        key = self.get_key()
        results = []

        def _remove_many(redis, values):
            for value in values:
                logger.debug('removing value %s from %s', value, key)
                result = redis.zrem(key, value)
                results.append(result)
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_remove_many, values)

        return results

    def remove_by_scores(self, scores):
        key = self.get_key()
        results = []

        def _remove_many(redis, scores):
            for score in scores:
                logger.debug('removing score %s from %s', score, key)
                result = redis.zremrangebyscore(key, score, score)
                results.append(result)
            return results

        # start a new map redis or go with the given one
        results = self._pipeline_if_needed(_remove_many, scores)

        return results

    def contains(self, value):
        '''
        Uses zscore to see if the given activity is present in our sorted set
        '''
        key = self.get_key()
        result = self.redis.zscore(key, value)
        activity_found = result is not None
        return activity_found

    def trim(self, max_length=None):
        '''
        Trim the sorted set to max length
        zremrangebyscore
        '''
        key = self.get_key()
        if max_length is None:
            max_length = self.max_length

        # map things to the funny redis syntax
        end = (max_length * -1) - 1

        removed = self.redis.zremrangebyrank(key, 0, end)
        logger.info('cleaning up the sorted set %s to a max of %s items' %
                    (key, max_length))
        return removed

    def get_results(self, start=None, stop=None):
        '''
        Retrieve results from redis using zrevrange
        O(log(N)+M) with N being the number of elements in the sorted set and M the number of elements returned.
        '''
        if self.sort_asc:
            redis_range_fn = self.redis.zrange
        else:
            redis_range_fn = self.redis.zrevrange

        # python [:2] gives 2 results, redis zrange 0:2 gives 3, so minus one
        if stop is None:
            stop = -1
        else:
            stop -= 1

        if start is None:
            start = 0

        key = self.get_key()
        redis_results = redis_range_fn(key, start, stop, withscores=True)

        return redis_results
