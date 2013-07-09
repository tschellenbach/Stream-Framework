from feedly.activity import AggregatedActivity
from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.base import BaseFeed
from feedly.storage.utils.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
import copy
import logging
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.storage.redis.activity_storage import RedisActivityStorage

logger = logging.getLogger(__name__)


class AggregatedFeed(BaseFeed):
    def get_aggregator(self):
        '''
        Returns the class used for aggregation
        '''
        aggregator_class = RecentVerbAggregator
        aggregator = aggregator_class()
        return aggregator


class RedisAggregatedFeed(AggregatedFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
    
    serializer_class = AggregatedActivitySerializer
    
#    def add_many(self, activity_ids, *args, **kwargs):
#        # start by getting the aggregator
#        aggregator = self.get_aggregator()
#        # aggregate the activities
#        aggregated_activities = aggregator.aggregate(activities)
#        
#        # get the current aggregated activities
#        current_activities = self[:self.max_length]
#        
#        
#        
#        self.timeline_storage.add_many(
#            self.key, activity_ids, *args, **kwargs)
#        
#        # trim to our max length
#        self.timeline_storage.trim(self.key, self.max_length)
#        return
    
#    def add_many(self, activities):
#        '''
#        Note this function is very specific to notifications, this won't
#        get you good performance characteristics in applications with longer
#        lists
#
#        Add many works as follows:
#        - retrieve all aggregated activities
#        - add the new activities to the existing ones
#        - update the values in Redis by sending several deletes and adds
#
#        Trim the sorted set to max length
#        Denormalize the unseen count
#        Send a pubsub publish
#        '''
#        value_score_pairs = []
#        remove_activities = {}
#        aggregator = self.get_aggregator()
#
#        # first stick the new activities in groups
#        aggregated_activities = aggregator.aggregate(activities)
#
#        # get the current aggregated activities
#        current_activities = self[:self.max_length]
#        current_activities_dict = dict(
#            [(a.group, a) for a in current_activities])
#
#        # see what we need to update
#        for activity in aggregated_activities:
#            if activity.group in current_activities_dict:
#                # update existing
#                current_activity = current_activities_dict[activity.group]
#                old_activity = copy.deepcopy(current_activity)
#                for a in activity.activities:
#                    current_activity.append(a)
#                new_activity = current_activity
#                # we should only do this the first time, verify things go well
#                if old_activity.group in remove_activities:
#                    raise ValueError('Thierry didnt expect this to happen')
#                remove_activities[old_activity.group] = old_activity
#            else:
#                # create a new activity
#                new_activity = activity
#                current_activities.append(new_activity)
#
#            # add the data to the to write list
#            value = self.serialize_activity(new_activity)
#            score = self.get_activity_score(new_activity)
#            value_score_pairs.append((value, score))
#
#        # pipeline all our writes to improve performance
#        # TODO: removed map just to be sure
#        # first remove the old notifications
#        delete_results = self.remove_many(remove_activities.values())
#
#        # add the data in batch
#        add_results = RedisSortedSetCache.add_many(self, value_score_pairs)
#
#        # make sure we trim to max length
#        trim_result = self.trim()
#
#        # return the current state of the notification feed
#        return current_activities
    

    
    


class OldAggregatedFeed(BaseFeed):

    '''
    An aggregated feed made for relatively small feeds
    It uses a sequential scan to detect if the group already exists
    Don't use this for feeds with a large max length
    '''
    
    key_format = 'aggregated_feed_%s'


    def get_aggregator(self):
        '''
        Returns the class used for aggregation
        '''
        aggregator_class = RecentVerbAggregator
        aggregator = aggregator_class()
        return aggregator

    def contains(self, activity):
        # get all the current aggregated activities
        aggregated = self[:self.max_length]
        activities = sum([list(a.activities) for a in aggregated], [])
        # make sure we don't modify things in place
        activities = copy.deepcopy(activities)
        activity = copy.deepcopy(activity)

        # we don't care about the time of the activity, just the contents
        activity.time = None
        for activity in activities:
            activity.time = None

        present = activity in activities
        return present

    def remove_many(self, aggregated_activities):
        '''
        Efficiently remove many activities
        '''
        scores = []
        for activity in aggregated_activities:
            if not isinstance(activity, AggregatedActivity):
                raise ValueError('we can only remove aggregated activities')
            score = self.get_activity_score(activity)
            scores.append(score)
        results = RedisSortedSetCache.remove_by_scores(self, scores)
        return results
