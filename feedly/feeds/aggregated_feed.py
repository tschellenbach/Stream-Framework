from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.sorted_feed import SortedFeed
from feedly.serializers.pickle_serializer import PickleSerializer
from feedly.structures.sorted_set import RedisSortedSetCache
from feedly.utils import datetime_to_epoch
import copy
import datetime
import logging
from feedly.activity import AggregatedActivity

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
                # we should only do this the first time, verify things go well
                if old_activity.group in remove_activities:
                    raise ValueError('Thierry didnt expect this to happen')
                remove_activities[old_activity.group] = old_activity
            else:
                # create a new activity
                new_activity = activity
                current_activities.append(new_activity)
            
            # add the data to the to write list
            value = self.serialize_activity(new_activity)
            score = self.get_activity_score(new_activity)
            value_score_pairs.append((value, score))

        # first remove the old notifications
        delete_results = self.remove_many(remove_activities.values())
        
        # add the data in batch
        add_results = RedisSortedSetCache.add_many(self, value_score_pairs)
        
        # make sure we trim to max length
        self.trim()
        
        # denormalize the count
        count = self.denormalize_count(current_activities)
        
        # send a pubsub request
        publish_result = self.redis.publish(self.pubsub_key, count)
        
        # return the current state of the notification feed
        return current_activities
    
    def denormalize_count(self, activities):
        '''
        Denormalize the number of unseen aggregated activities to the key
        defined in self.count_key
        '''
        # denormalize the count, without querying redis again
        activities.sort(key=lambda x: x.last_seen, reverse=True)
        current_activities = activities[:self.max_length]
        count = self.count_unseen(current_activities)
        logger.debug('denormalizing count %s', count)
        self.redis.set(self.count_key, count)
        
        return count
    
    def update(self, update_dict, new_activities):
        pass
    
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
    
    def mark_all(self, seen=True, read=None):
        '''
        Mark all the entries as seen or read
        '''
        # get the current aggregated activities
        activities = self[:self.max_length]
        # create the update dict
        update_dict = {}
        
        for activity in activities:
            changed = False
            old_activity = copy.deepcopy(activity)
            if seen is True and not activity.seen_at:
                activity.seen_at = datetime.datetime.today()
                changed = True
            if read is True and not activity.read_at:
                activity.read_at = datetime.datetime.today()
                changed = True
                
            if changed:
                update_dict[old_activity] = activity
        
        # now add the new ones and remove the old ones in one atomic operation
        to_delete = []
        to_add = []

        for old, new in update_dict.items():
            new_value = self.serialize_activity(new)
            new_score = self.get_activity_score(new)
            to_delete.append(old)
            
            to_add.append((new_value, new_score))
            
        if to_delete:
            delete_results = self.remove_many(to_delete)
            
        # add the data in batch
        if to_add:
            add_results = RedisSortedSetCache.add_many(self, to_add)
        
        # denormalize the count
        count = self.denormalize_count(activities)
        
        # return the new activities
        return activities
        
    def contains(self, activity):
        # get all the current aggregated activities
        aggregated = self[:self.max_length]
        activities = sum([a.activities for a in aggregated], [])
        activity_dicts = [a.__dict__ for a in activities]
        present = activity.__dict__ in activity_dicts
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
    
    def get_activity_score(self, aggregated_activity):
        '''
        Ensures a unique score by appending the verb id at the end
        '''
        verb_part = ''.join(map(str, [v.id for v in aggregated_activity.verbs]))
        epoch = datetime_to_epoch(aggregated_activity.last_seen)
        score = float(unicode(epoch) + verb_part)
        return score
    
    def get_results(self, start, stop):
        redis_results = AggregatedFeed.get_results(self, start, stop)
        enriched_results = self.deserialize_activities(redis_results)
        return enriched_results
        

