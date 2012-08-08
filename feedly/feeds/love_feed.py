from django.contrib.auth.models import User
from entity.cache_objects import entity_cache
from feedly.feed_managers.love_feedly import LoveFeedly
from feedly.feeds.sorted_feed import SortedFeed
from feedly.marker import FeedEndMarker, FEED_END
from feedly.serializers.love_activity_serializer import LoveActivitySerializer
from feedly.structures.hash import DatabaseFallbackHashCache
from feedly.structures.sorted_set import RedisSortedSetCache
from feedly.utils import epoch_to_datetime, datetime_to_epoch, time_asc
from feedly.verbs.base import Love as LoveVerb
import logging
from feedly.serializers.activity_serializer import ActivitySerializer
logger = logging.getLogger(__name__)


class LoveFeedItemCache(DatabaseFallbackHashCache):
    key_format = 'feedly:love_feed_items:%s'
    
    def get_many_from_database(self, missing_keys):
        '''
        Return a dictionary with the serialized values for the missing keys
        '''
        database_results = {}
        if missing_keys:
            from entity.models import Love
            ids = [k.split(',') for k in missing_keys]
            love_ids = [int(love_id) for verb_id, love_id in ids]
            values = Love.objects.filter(id__in=love_ids).values_list('id', 'user_id', 'created_at', 'entity_id', 'influencer_id')
            for value_tuple in values:
                love_id = int(value_tuple[0])
                user_id, created_at, entity_id, influencer_id = value_tuple[1:]
                love = Love(user_id=int(user_id), created_at=created_at, entity_id=entity_id, id=love_id, influencer_id=int(influencer_id))
                activity = love.create_activity()
                
                serializer = LoveActivitySerializer()
                serialized_activity = serializer.dumps(activity)
                key = ','.join(map(str, [LoveVerb.id, love_id]))
                database_results[key] = serialized_activity
            
        return database_results
        

class LoveFeed(SortedFeed, RedisSortedSetCache):
    '''
    The love Feed class
    
    It implements the feed logic
    Actual operations on redis should be handled by the RedisSortedSetCache object
    '''
    default_max_length = 24 * 150
    key_format = 'feedly:love_feed:%s'
    manager = LoveFeedly
    
    serializer_class = LoveActivitySerializer
    
    def __init__(self, user_id, redis=None, max_length=None):
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
        self.item_cache = LoveFeedItemCache('global')
        self.key = self.key_format % user_id
        self._max_length = max_length
        
    def add(self, activity):
        '''
        Make sure results are actually cleared to max items
        '''
        activities = [activity]
        result = self.add_many(activities)[0]
        return result
    
    def add_many(self, activities):
        '''
        We use pipelining for doing multiple adds
        Alternatively we could also send multiple adds to one call.
        Don't see a reason for that though
        '''
        value_score_pairs = []
        key_value_pairs = []
        for activity in activities:
            value = self.serialize_activity(activity)
            score = self.get_activity_score(activity)
            
            #if its real data write the id to the redis hash cache
            if not isinstance(activity, FeedEndMarker):
                key_value_pairs.append((activity.serialization_id, value))
                
            value_score_pairs.append((activity.serialization_id, score))
            
        # we need to do this sequentially, otherwise there's a risk of broken reads
        self.item_cache.set_many(key_value_pairs)
        results = RedisSortedSetCache.add_many(self, value_score_pairs)
        
        #make sure we trim to max length
        self.trim()
        return results
    
    def contains(self, activity):
        '''
        Uses zscore to see if the given activity is present in our sorted set
        '''
        result = RedisSortedSetCache.contains(self, activity.serialization_id)
        activity_found = bool(result)
        return activity_found
    
    def remove(self, activity):
        '''
        Delegated to remove many
        '''
        activities = [activity]
        result = self.remove_many(activities)[0]
        return result
        
    def remove_many(self, activities):
        '''
        Efficiently remove many activities
        '''
        values = []
        for activity in activities:
            values.append(activity.serialization_id)
        results = RedisSortedSetCache.remove_many(self, values)
        
        return results
    
    def finish(self):
        '''
        Mark the feed as finished, this shows us if we need to query after reaching
        the end of the redis sorted set
        '''
        end_marker = FeedEndMarker()
        self.add(end_marker)
    
    @property
    def max_length(self):
        '''
        Allow us to overwrite the max length at a per user level
        '''
        max_length = getattr(self, '_max_length', self.default_max_length) or self.default_max_length
        return max_length
    
    def serialize_activity(self, activity):
        '''
        Serialize the activity into something we can store in Redis
        '''
        serialized_activity = self.serializer.dumps(activity)
        return serialized_activity
    
    def get_activity_score(self, activity):
        #score = datetime_to_epoch(activity.time)
        score = getattr(activity, 'object_id', 1)
        return score
    
    def deserialize_activities(self, activities):
        '''
        Reverse the serialization
        '''
        activity_ids = [activity_id for activity_id, score in activities if not activity_id == FEED_END]
        activity_dict = self.item_cache.get_many(activity_ids)
        
        activity_objects = []
        for activity_id, score in activities:
            serialized_activity = activity_dict.get(activity_id) or activity_id
            activity = self.serializer.loads(serialized_activity)
            #time_ = epoch_to_datetime(score)
            #activity.time = time_
            activity_objects.append(activity)
        return activity_objects
            
    def get_results(self, start=None, stop=None):
        '''
        Get results from redis
        '''
        results = self.get_redis_results(start, stop)
        return results
    
    def get_redis_results(self, start=None, stop=None):
        '''
        Retrieve results from redis using zrevrange
        O(log(N)+M) with N being the number of elements in the sorted set and M the number of elements returned.
        '''
        key = self.get_key()
        redis_results = self.redis.zrevrange(key, start, stop, withscores=True)
        enriched_results = self.deserialize_activities(redis_results)
        return enriched_results
    
    def get_results_by_date(self, start_epoch, limit=None):
        '''
        Filter based on date
        '''
        key = self.get_key()
        start = num = None
        if limit:
            start = 0
            num = limit
        redis_results = self.redis.zrangebyscore(key, start_epoch, '+inf', start=start, num=num, withscores=True)
        enriched_results = self._deserialize_activities(redis_results)
        return enriched_results
    
    def get_recent(self, start_time=None, limit=None):
        '''
        Only retrieve the recent items
        '''
        if not start_time:
            time_ = time_asc()
            start_time = time_ - 24 * 60 * 60
        enriched_results = self.get_results_by_date(start_time, limit=limit)
        return enriched_results
    

class DatabaseFallbackLoveFeed(LoveFeed):
    '''
    Version of the Love Feed which falls back to the database if no data is present
    It users the FeedEndMarker to know the difference between missing
    data and the end of the Cache
    
    We have to make really sure we don't end up querying the old system without
    primary keys
    '''
    db_max_length = 24 * 150
    
    def __init__(self, user_id, sort_asc=False, redis=None, max_length=None, pk__gte=None, pk__lte=None):
        '''
        '''
        LoveFeed.__init__(self, user_id, redis=redis, max_length=max_length)
        
        #some support for database and sorted set filtering
        self.pk__gte = pk__gte
        self.pk__lte = pk__lte
        self.sort_asc = sort_asc
        self._set_filter()
    
    def _set_filter(self):
        self._filtered = self.pk__gte is not None or self.pk__lte is not None
        self.redis_pk_from = self.pk__gte
        self.redis_pk_to = self.pk__lte
        if self.redis_pk_from is None:
            self.redis_pk_from = '-inf'
        if self.redis_pk_to is None:
            self.redis_pk_to = '+inf'
    
    def get_results(self, start, stop):
        '''
        Get the results either from redis or from the database.
        
        If we reach the end of the database results mark the redis cache as finished.
        '''
        key = self.get_key()
        #make sure we have a stop value
        if stop is None:
            raise ValueError('Please provide a stop value, got %r', stop)
        
        #start by getting the Redis results
        redis_results = self.get_redis_results(start, stop)
        required_items = stop - start
        enough_results = len(redis_results) >= required_items
        self.source = 'redis'
        
        #the FeedEndMarker indicates if we reached the end of the list
        feed_end_marker = None
        end_reached = redis_results and isinstance(redis_results[-1], FeedEndMarker)
        if end_reached:
            feed_end_marker = redis_results.pop()
        
        #fallback to the database if possible
        if not end_reached and (not redis_results or not enough_results):
            self.source = 'db'
            db_queryset = self.get_queryset_results(start, stop)
            db_results = list(db_queryset)
            db_enough_results = len(db_results) >= required_items
            end_reached = not db_enough_results or stop == self.db_max_length
            #only do these things if we're are at the beginning of a list and not filtering
            logger.info('setting cache for type %s with len %s', key, len(db_results))
            #only cache when we have no results, to prevent duplicates
            self.cache(db_results)
            
            #mark that there is no more data
            #prevents us from endlessly quering empty lists
            if end_reached:
                self.finish()
                
            results = db_results
            logger.info('retrieved %s to %s from db and not from cache with key %s' % (start, stop, key))
        else:
            results = redis_results[:required_items]
            logger.info('retrieved %s to %s from cache on key %s' % (start, stop, key))
            
        #make sure we return the right number of results
        if len(results) > required_items:
            raise ValueError('We should never have more than we ask for, start %s, stop %s', start, stop)
            
        #hack to support paginator
        for result in results:
            result.id = result.object_id
            
        return results
    
    def get_redis_results(self, start=None, stop=None):
        '''
        Retrieve results from redis using zrevrange
        O(log(N)+M) with N being the number of elements in the sorted set and M the number of elements returned.
        '''
        if stop is None or start is None:
            num = None
            start = None
        elif stop is not None and start is not None:
            num = 1 + stop - start
        
        if self.sort_asc:
            min_max_args = (self.redis_pk_from, self.redis_pk_to)
            redis_range_fn = self.redis.zrangebyscore
        else:
            min_max_args = (self.redis_pk_to, self.redis_pk_from)
            redis_range_fn = self.redis.zrevrangebyscore
        
        key = self.get_key()
        redis_results = redis_range_fn(self.key, *min_max_args, start=start, num=num, withscores=True)
        #redis_results = self.redis.zrevrange(key, start, stop, withscores=True)
        enriched_results = self.deserialize_activities(redis_results)
        return enriched_results
    
    def get_queryset_results(self, start, stop):
        '''
        Get the results from the database and turn the loves
        into their activity counterparts
        '''
        latest_loves = self.get_queryset()
        if self.pk__gte:
            latest_loves = latest_loves.filter(pk__gte=self.pk__gte)
        if self.pk__lte:
            latest_loves = latest_loves.filter(pk__lte=self.pk__lte)
        if self.sort_asc:
            latest_loves = latest_loves.order_by('id')
        else:
            latest_loves = latest_loves.order_by('-id')
        
        if stop is None or start is None:
            num = None
            start = None
        elif stop is not None and start is not None:
            num = stop - start
            
        latest_loves = latest_loves[:self.db_max_length][:num]
        activities = []
        for love in latest_loves:
            activity = love.create_activity()
            activities.append(activity)
        return activities
    
    def get_queryset(self):
        '''
        Returns the profile.following loves queryset
        '''
        user = User.objects.get_cached_user(self.user_id)
        profile = user.get_profile()
        loves = profile._following_loves()
        return loves
    
    def cache(self, activities):
        '''
        This method is called if we get data from the database which isn't
        in redis yet
        '''
        for activity in activities:
            self.add(activity)
        return activities


def convert_activities_to_loves(activities):
    '''
    Turns our activities into loves
    '''
    from entity.models import Love
    user_ids = [a.actor_id for a in activities]
    entity_ids = [a.extra_context['entity_id'] for a in activities]
    user_dict = User.objects.get_cached_users(user_ids)
    entity_dict = entity_cache[entity_ids]
    
    loves = []
    for activity in activities:
        activity.actor = user_dict[activity.actor_id]
        entity_id = activity.extra_context['entity_id']
        activity.entity = entity_dict[entity_id]
        love = Love(
            id=activity.object_id, user_id=activity.actor_id,
            entity_id=entity_id, created_at=activity.time
        )
        love.activity = activity
        loves.append(love)
    return loves




