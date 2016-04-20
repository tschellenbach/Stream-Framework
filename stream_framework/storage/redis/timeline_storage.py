from stream_framework.storage.base import BaseTimelineStorage
from stream_framework.storage.redis.structures.sorted_set import RedisSortedSetCache
from stream_framework.storage.redis.connection import get_redis_connection
from stream_framework.utils.five import long_t
import six



class TimelineCache(RedisSortedSetCache):
    sort_asc = False


class RedisTimelineStorage(BaseTimelineStorage):

    def get_cache(self, key):
        redis_server = self.options.get('redis_server', 'default')
        cache = TimelineCache(key, redis_server=redis_server)
        return cache

    def contains(self, key, activity_id):
        cache = self.get_cache(key)
        contains = cache.contains(activity_id)
        return contains

    def get_slice_from_storage(self, key, start, stop, filter_kwargs=None, ordering_args=None):
        '''
        Returns a slice from the storage
        :param key: the redis key at which the sorted set is located
        :param start: the start
        :param stop: the stop
        :param filter_kwargs: a dict of filter kwargs
        :param ordering_args: a list of fields used for sorting

        **Example**::
           get_slice_from_storage('feed:13', 0, 10, {activity_id__lte=10})
        '''
        cache = self.get_cache(key)

        # parse the filter kwargs and translate them to min max
        # as used by the get results function
        valid_kwargs = [
            'activity_id__gte', 'activity_id__lte',
            'activity_id__gt', 'activity_id__lt',
        ]
        filter_kwargs = filter_kwargs or {}
        result_kwargs = {}
        for k in valid_kwargs:
            v = filter_kwargs.pop(k, None)
            if v is not None:
                if not isinstance(v, (float, six.integer_types)):
                    raise ValueError(
                        'Filter kwarg values should be floats, int or long, got %s=%s' % (k, v))

                # By default, the interval specified by min_score and max_score is closed (inclusive).
                # It is possible to specify an open interval (exclusive) by prefixing the score with the character (
                _, direction = k.split('__')
                equal = 'te' in direction

                if 'gt' in direction:
                    if not equal:
                        v = '(' + str(v)
                    result_kwargs['min_score'] = v
                else:
                    if not equal:
                        v = '(' + str(v)
                    result_kwargs['max_score'] = v
        # complain if we didn't recognize the filter kwargs
        if filter_kwargs:
            raise ValueError('Unrecognized filter kwargs %s' % filter_kwargs)

        if ordering_args:
            if len(ordering_args) > 1:
                raise ValueError('Too many order kwargs %s' % ordering_args)

            if '-activity_id' in ordering_args:
                # descending sort
                cache.sort_asc = False
            elif 'activity_id' in ordering_args:
                cache.sort_asc = True
            else:
                raise ValueError('Unrecognized order kwargs %s' % ordering_args)

        # get the actual results
        key_score_pairs = cache.get_results(start, stop, **result_kwargs)
        score_key_pairs = [(score, data) for data, score in key_score_pairs]

        return score_key_pairs

    def get_batch_interface(self):
        return get_redis_connection(
            server_name=self.options.get('redis_server', 'default')
        ).pipeline(transaction=False)

    def get_index_of(self, key, activity_id):
        cache = self.get_cache(key)
        index = cache.index_of(activity_id)
        return index

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        cache = self.get_cache(key)
        # turn it into key value pairs
        scores = map(long_t, activities.keys())
        score_value_pairs = list(zip(scores, activities.values()))
        result = cache.add_many(score_value_pairs)
        for r in result:
            # errors in strings?
            # anyhow raise them here :)
            if hasattr(r, 'isdigit') and not r.isdigit():
                raise ValueError('got error %s in results %s' % (r, result))
        return result

    def remove_from_storage(self, key, activities, batch_interface=None):
        cache = self.get_cache(key)
        results = cache.remove_many(activities.values())
        return results

    def count(self, key):
        cache = self.get_cache(key)
        return int(cache.count())

    def delete(self, key):
        cache = self.get_cache(key)
        cache.delete()

    def trim(self, key, length, batch_interface=None):
        cache = self.get_cache(key)
        cache.trim(length)
