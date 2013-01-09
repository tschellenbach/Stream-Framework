from feedly.feeds.sorted_feed import SortedFeed
from feedly.serializers.pickle_serializer import PickleSerializer
from feedly.structures.sorted_set import RedisSortedSetCache
from feedly.aggregators.base import RecentVerbAggregator
import copy
from feedly.utils import datetime_to_epoch


class AggregatedFeed(SortedFeed, RedisSortedSetCache):
    def get_aggregator(self):
        aggregator_class = RecentVerbAggregator
        aggregator = aggregator_class()
        return aggregator


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
        Note this function is very specific to notifications, this won't
        get you good performance characteristics in applications with longer
        lists
        
        Add many works as follows:
        - retrieve all aggregated activities
        - add the new activities to the existing ones
        - update the values in Redis by sending several deletes and adds
        
        Trim the sorted set to max length
        '''
        value_score_pairs = []
        remove_activities = []
        aggregator = self.get_aggregator()
        
        #first stick the new activities in groups
        aggregated_activities = aggregator.aggregate(activities)
        
        #get the current aggregated activities
        current_activities = self[:self.max_length]
        current_activities_dict = dict([(a.group, a) for a in current_activities])
        
        #see what we need to update
        for activity in aggregated_activities:
            if activity.group in current_activities_dict:
                #update existing
                current_activity = current_activities_dict[activity.group]
                old_activity = copy.deepcopy(current_activity)
                for a in activity.activities:
                    current_activity.append(a)
                new_activity = current_activity
                remove_activities.append(old_activity)
            else:
                #create a new activity
                new_activity = activity
            value = self.serialize_activity(new_activity)
            score = self.get_activity_score(new_activity)
            value_score_pairs.append((value, score))

        #first remove the old notifications
        delete_results = self.remove_many(remove_activities)
        
        #add the data in batch
        add_results = RedisSortedSetCache.add_many(self, value_score_pairs)
        print int(self.count())

        #make sure we trim to max length
        self.trim()
        return add_results
    
    def contains(self, activity):
        #get all the current aggregated activities
        aggregated = self[:self.max_length]
        activities = sum([a.activities for a in aggregated], [])
        activity_dicts = [a.__dict__ for a in activities]
        present = activity.__dict__ in activity_dicts
        return present
    
    def remove_many(self, activities):
        '''
        Efficiently remove many activities
        '''
        values = []
        for activity in activities:
            score = self.get_activity_score(activity)
            values.append(score)
        results = RedisSortedSetCache.remove_many(self, values)

        return results
    
    def get_activity_score(self, aggregated_activity):
        score = datetime_to_epoch(aggregated_activity.last_seen)
        return score
    
    def get_results(self, start, stop):
        redis_results = AggregatedFeed.get_results(self, start, stop)
        enriched_results = self.deserialize_activities(redis_results)
        return enriched_results
        

