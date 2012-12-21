from feedly.feeds.sorted_feed import SortedFeed
from feedly.serializers.pickle_serializer import PickleSerializer
from feedly.structures.sorted_set import RedisSortedSetCache


class AggregatedFeed(SortedFeed, RedisSortedSetCache):
    pass


class NotificationFeed(AggregatedFeed):
    max_length = 35
    serializer_class = PickleSerializer
    
    def __init__(self, user_id, redis=None):
        '''
        '''
        RedisSortedSetCache.__init__(self, user_id, redis=redis)
        #input validation
        if not isinstance(user_id, int):
            raise ValueError('user id should be an int, found %r' % user_id)
        #support for different serialization schemes
        self.serializer = self.serializer_class()
        #support for pipelining redis
        self.user_id = user_id
        self.key = self.key_format % user_id

    def add_many(self, activities):
        '''
        TODO, Implement this :)
        '''
        value_score_pairs = []
        key_value_pairs = []
        for activity in activities:
            value = self.serialize_activity(activity)
            score = self.get_activity_score(activity)

            if not isinstance(activity, FeedEndMarker):
                key_value_pairs.append((activity.serialization_id, value))

            value_score_pairs.append((activity.serialization_id, score))

        # we need to do this sequentially, otherwise there's a risk of broken reads
        self.item_cache.set_many(key_value_pairs)
        results = RedisSortedSetCache.add_many(self, value_score_pairs)

        #make sure we trim to max length
        self.trim()
        return results