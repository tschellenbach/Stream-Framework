from stream_framework.utils.functional import lazy
from stream_framework.storage.redis.structures.hash import BaseRedisHashCache
from stream_framework.storage.redis.structures.list import BaseRedisListCache
from stream_framework.utils import chunks
import six
import logging
logger = logging.getLogger(__name__)


class RedisSortedSetCache(BaseRedisListCache, BaseRedisHashCache):
    sort_asc = False

    def count(self):
        '''
        Returns the number of elements in the sorted set
        '''
        key = self.get_key()
        redis_result = self.redis.zcard(key)
        # lazily convert this to an int, this keeps it compatible with
        # distributed connections
        redis_count = lambda: int(redis_result)
        lazy_factory = lazy(redis_count, *six.integer_types)
        lazy_object = lazy_factory()
        return lazy_object

    def index_of(self, value):
        '''
        Returns the index of the given value
        '''
        if self.sort_asc:
            redis_rank_fn = self.redis.zrank
        else:
            redis_rank_fn = self.redis.zrevrank
        key = self.get_key()
        result = redis_rank_fn(key, value)
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
        scores = list(zip(*score_value_pairs))[0]
        msg_format = 'Please send floats as the first part of the pairs got %s'
        numeric_types = (float,) + six.integer_types
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
        if self.sort_asc:
            begin = max_length
            end = -1
        else:
            begin = 0
            end = (max_length * -1) - 1

        removed = self.redis.zremrangebyrank(key, begin, end)
        logger.info('cleaning up the sorted set %s to a max of %s items' %
                    (key, max_length))
        return removed

    def get_results(self, start=None, stop=None, min_score=None, max_score=None):
        '''
        Retrieve results from redis using zrevrange
        O(log(N)+M) with N being the number of elements in the sorted set and M the number of elements returned.
        '''
        if self.sort_asc:
            redis_range_fn = self.redis.zrangebyscore
        else:
            redis_range_fn = self.redis.zrevrangebyscore

        # -1 means infinity
        if stop is None:
            stop = -1

        if start is None:
            start = 0

        if stop != -1:
            limit = stop - start
        else:
            limit = -1

        key = self.get_key()

        # some type validations
        if min_score and not isinstance(min_score, (float, str, six.integer_types)):
            raise ValueError(
                'min_score is not of type float, int, long or str got %s' % min_score)
        if max_score and not isinstance(max_score, (float, str, six.integer_types)):
            raise ValueError(
                'max_score is not of type float, int, long or str got %s' % max_score)

        if min_score is None:
            min_score = '-inf'
        if max_score is None:
            max_score = '+inf'

        # handle the starting score support
        results = redis_range_fn(
            key, start=start, num=limit, withscores=True, min=min_score, max=max_score)
        return results
