from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.sorted_feed import SortedFeed
from feedly.serializers.pickle_serializer import PickleSerializer
from feedly.structures.sorted_set import RedisSortedSetCache
from feedly.utils import datetime_to_epoch
import copy
import datetime
import logging

logger = logging.getLogger(__name__)


class AggregatedFeed(SortedFeed, RedisSortedSetCache):
    def get_aggregator(self):
        aggregator_class = RecentVerbAggregator
        aggregator = aggregator_class()
        return aggregator


class NotificationFeed(AggregatedFeed):
    max_length = 35
    serializer_class = PickleSerializer
    
    # key format for storing the sorted set
    key_format = 'notification_feed:1:user:%s'
    # the format we use to denormalize the count
    notification_count_format = 'notification_feed:1:user:%(user_id)s:count'
    # the format we use to send the pubsub update
    notification_pubsub_format = 'notification_feed:1:user:%(user_id)s:pubsub'
    
    def __init__(self, user_id, redis=None):
        '''
        User id (the user for which we want to read/write notifications)
        '''
        RedisSortedSetCache.__init__(self, user_id, redis=redis)
        # input validation
        if not isinstance(user_id, int):
            raise ValueError('user id should be an int, found %r' % user_id)
        # support for different serialization schemes
        self.serializer = self.serializer_class()
        # support for pipelining redis
        self.user_id = user_id
        
        # write the key locations
        format_dict = dict(user_id=user_id)
        self.key = self.key_format % user_id
        self.count_key = self.notification_count_format % format_dict
        self.pubsub_key = self.notification_pubsub_format % format_dict
        
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
        Denormalize the unseen count
        Send a pubsub publish
        '''
        value_score_pairs = []
        remove_activities = {}
        aggregator = self.get_aggregator()
        
        # first stick the new activities in groups
        aggregated_activities = aggregator.aggregate(activities)
        
        # get the current aggregated activities
        current_activities = self[:self.max_length]
        current_activities_dict = dict([(a.group, a) for a in current_activities])
        
        # see what we need to update
        for activity in aggregated_activities:
            if activity.group in current_activities_dict:
                # update existing
                current_activity = current_activities_dict[activity.group]
                old_activity = copy.deepcopy(current_activity)
                for a in activity.activities:
                    current_activity.append(a)
                new_activity = current_activity
                # we should only do this the first time
                if old_activity.group not in remove_activities:
                    remove_activities[old_activity.group] = old_activity
            else:
                # create a new activity
                new_activity = activity
                current_activities.append(new_activity)
            value = self.serialize_activity(new_activity)
            score = self.get_activity_score(new_activity)
            value_score_pairs.append((value, score))

        # first remove the old notifications
        delete_results = self.remove_many(remove_activities.values())
        
        # add the data in batch
        add_results = RedisSortedSetCache.add_many(self, value_score_pairs)

        # make sure we trim to max length
        self.trim()
        
        # denormalize the count, without querying redis again
        current_activities.sort(key=lambda x: x.last_seen, reverse=True)
        current_activities = current_activities[:self.max_length]
        count = self.count_unseen(current_activities)
        logger.debug('denormalizing count %s', count)
        
        # send a pubsub request
        publish_result = self.redis.publish(self.pubsub_key, count)
        
        # return the current state of the notification feed
        return current_activities
    
    def count_unseen(self, activities=None):
        '''
        Counts the number of aggregated activities which are unseen
        '''
        count = 0
        if activities is None:
            activities = self[:self.max_length]
        for a in activities:
            if not a.is_seen():
                count += 1
        return count
    
    def mark(self, group, seen=True, read=None):
        groups = [group]
        self.mark_many(groups, seen=seen, read=read)
    
    def mark_many(self, groups, seen=True, read=None):
        # get the current aggregated activities
        current_activities = self[:self.max_length]
        current_activities_dict = dict([(a.group, a) for a in current_activities])
        
        # find the changed group
        activity = current_activities_dict[group]
        if seen is True and not activity.seen_at:
            activity.seen_at = datetime.datetime.today()
        if read is True and not activity.read_at:
            activity.read_at = datetime.datetime.today()
        
    def contains(self, activity):
        # get all the current aggregated activities
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
        

