from feedly.feeds.aggregated_feed import AggregatedFeed
import copy
import datetime
import json
import logging
from feedly.storage.redis.timeline_storage import RedisTimelineStorage
from feedly.storage.redis.activity_storage import RedisActivityStorage

logger = logging.getLogger(__name__)


class NotificationFeed(AggregatedFeed):

    '''
    Similar to an aggregated feed, but adds
    - denormalized counts
    - pubsub signals
    For now this is entirely tied to Redis
    '''
    default_max_length = 99

    # key format for storing the sorted set
    key_format = 'notification_feed:1:user:%(user_id)s'
    # the format we use to denormalize the count
    count_format = 'notification_feed:1:user:%(user_id)s:count'
    # the key used for locking
    lock_format = 'notification_feed:1:user:%s:lock'
    # the main channel to publish
    pubsub_main_channel = 'juggernaut'

    def __init__(self, user_id, **kwargs):
        '''
        User id (the user for which we want to read/write notifications)
        '''
        AggregatedFeed.__init__(self, user_id, **kwargs)

        # location to which we denormalize the count
        self.format_dict = dict(user_id=user_id)
        self.count_key = self.count_format % self.format_dict
        # set the pubsub key if we're using it
        self.pubsub_key = user_id
        self.lock_key = self.lock_format % self.format_dict
        from feedly.storage.redis.connection import get_redis_connection
        self.redis = get_redis_connection()

    def count_dict(self, count):
        return dict(unread_count=count, unseen_count=count)

    def publish_count(self, count):
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
            aggregated_activities = self[:self.max_length]
            # create the update dict
            update_dict = {}

            for aggregated_activity in aggregated_activities:
                changed = False
                old_activity = copy.deepcopy(aggregated_activity)
                if seen is True and not aggregated_activity.is_seen():
                    aggregated_activity.seen_at = datetime.datetime.today()
                    changed = True
                if read is True and not aggregated_activity.is_read():
                    aggregated_activity.read_at = datetime.datetime.today()
                    changed = True

                if changed:
                    update_dict[old_activity] = aggregated_activity

            # now add the new ones and remove the old ones in one atomic
            # operation
            to_delete = []
            to_add = []

            for old, new in update_dict.items():
                to_delete.append(old)
                to_add.append(new)

            # delete first
            if to_delete:
                self.timeline_storage.remove_many(self.key, to_delete)

            # add the data in batch
            if to_add:
                self.timeline_storage.add_many(self.key, to_add)

            # denormalize the count
            self.denormalize_count(aggregated_activities)

            # return the new activities
            return aggregated_activities


class RedisNotificationFeed(NotificationFeed):
    timeline_storage_class = RedisTimelineStorage
    activity_storage_class = RedisActivityStorage
