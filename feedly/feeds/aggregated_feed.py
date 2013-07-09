from feedly.aggregators.base import RecentVerbAggregator, NotificationAggregator
from feedly.feeds.base import BaseFeed
import copy
import logging
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.storage.redis.activity_storage import RedisActivityStorage
import datetime
import json
from feedly.utils import sign_value

logger = logging.getLogger(__name__)


class AggregatedFeed(BaseFeed):
    '''
    Aggregated feeds are somewhat different
    
    - Aggregator classes aggregate activities into aggregated activities
    - We need to update aggregated activities instead of only appending
    - Serialization is different
    
    This can be used for smart feeds (like Facebook) or possibly
    notification systems
    '''
    aggregator_class = RecentVerbAggregator
    
    def add_many(self, activities, *args, **kwargs):
        # start by getting the aggregator
        aggregator = self.get_aggregator()
        
        # aggregate the activities
        new_activities = aggregator.aggregate(activities)
        
        # get the current aggregated activities
        current_activities = self[:self.max_length]
        
        # merge the current activities with the new ones
        new, changed = aggregator.merge(current_activities, new_activities)
        # new ones we insert, changed we do a delete and insert
        to_remove = []
        to_add = new
        if changed:
            # sorry about the very python specific hack :)
            to_remove = zip(*changed)[0]
            to_add += zip(*changed)[1]
        
        # remove those which changed
        self.timeline_storage.remove_many(
            self.key, to_remove, *args, **kwargs)
        # now add the new ones
        '''
        TODO
        So where do I serialize and deserialize the activity...
        '''
        to_add = [(a, a.serialization_id) for a in to_add]
        self.timeline_storage.add_many(
            self.key, to_add, *args, **kwargs)
        print 'now', self[:10], 'after', to_add
        # now trim
        self.timeline_storage.trim(self.key, self.max_length)
        
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
    
    def get_aggregator(self):
        '''
        Returns the class used for aggregation
        '''
        aggregator = self.aggregator_class()
        return aggregator
    

class RedisAggregatedFeed(AggregatedFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
    
    
class NotificationFeed(AggregatedFeed):
    '''
    Similar to an aggregated feed, but adds
    - denormalized counts
    - redis pubsub signals
    '''
    max_length = 99
    # key format for storing the sorted set
    key_format = 'notification_feed:1:user:%s'
    # the format we use to denormalize the count
    count_format = 'notification_feed:1:user:%(user_id)s:count'
    # the key used for locking
    lock_format = 'notification_feed:1:user:%s:lock'
    # the main channel to publish
    pubsub_main_channel = 'juggernaut'
    
    aggregator_class = NotificationAggregator

    def __init__(self, user_id, redis=None):
        '''
        User id (the user for which we want to read/write notifications)
        '''
        AggregatedFeed.__init__(self, user_id, redis=redis)
        # location to which we denormalize the count
        self.count_key = self.count_format % self.format_dict
        # set the pubsub key if we're using it
        if self.pubsub_main_channel:
            self.pubsub_key = sign_value(user_id)
        self.lock_key = self.lock_format % self.format_dict

    def count_dict(self, count):
        return dict(unread_count=count, unseen_count=count)

    def publish_count(self, count):
        if self.pubsub_main_channel:
            count_data = json.dumps(self.count_dict(count))
            data = {'channel': self.pubsub_key, 'data': count_data}
            encoded_data = json.dumps(data)
            self.redis.publish(self.pubsub_main_channel, encoded_data)

    def add_many(self, activities):
        with self.redis.lock(self.lock_key, timeout=2):
            current_activities = AggregatedFeed.add_many(self, activities)
            # denormalize the count
            count = self.denormalize_count(current_activities)
            # return the current state of the notification feed
            return current_activities

    def try_denormalized_count(self):
        '''
        A failure to load the count shouldnt take down the entire site
        '''
        try:
            result = self.get_denormalized_count()
            return result
        except Exception, e:
            import sys
            logger.warn(u'Notification: Get denormalized count error %s' % e,
                        exc_info=sys.exc_info(), extra={
                        'data': {
                            'body': unicode(e),
                        }
                        })
            # hide behind the zero
            result = 0
        return result

    def get_denormalized_count(self):
        '''
        Returns the denormalized count stored in self.count_key
        '''
        result = self.redis.get(self.count_key) or 0
        result = int(result)
        return result

    def denormalize_count(self, activities):
        '''
        Denormalize the number of unseen aggregated activities to the key
        defined in self.count_key
        '''
        activities.sort(key=lambda x: x.updated_at, reverse=True)
        current_activities = activities[:self.max_length]
        count = self.count_unseen(current_activities)
        logger.debug('denormalizing count %s', count)
        stored_count = self.redis.get(self.count_key)
        if stored_count is None or stored_count != str(count):
            self.redis.set(self.count_key, count)
            self.publish_count(count)
        return count

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
        # TODO refactor this code
        with self.redis.lock(self.lock_key, timeout=2):
            # get the current aggregated activities
            activities = self[:self.max_length]
            # create the update dict
            update_dict = {}

            for activity in activities:
                changed = False
                old_activity = copy.deepcopy(activity)
                if seen is True and not activity.is_seen():
                    activity.seen_at = datetime.datetime.today()
                    changed = True
                if read is True and not activity.is_read():
                    activity.read_at = datetime.datetime.today()
                    changed = True

                if changed:
                    update_dict[old_activity] = activity

            # now add the new ones and remove the old ones in one atomic
            # operation
            to_delete = []
            to_add = []

            for old, new in update_dict.items():
                new_value = self.serialize_activity(new)
                new_score = self.get_activity_score(new)
                to_delete.append(old)

                to_add.append((new_value, new_score))

            # pipeline all our writes to improve performance
            # Update: removed self.map(), multithreaded behaviour seems bugged
            if to_delete:
                delete_results = self.remove_many(to_delete)

            # add the data in batch
            if to_add:
                add_results = RedisSortedSetCache.add_many(self, to_add)

            # denormalize the count
            count = self.denormalize_count(activities)

            # return the new activities
            return activities
    

