from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.serializers.aggregated_activity_serializer import \
    NotificationSerializer
from stream_framework.storage.redis.timeline_storage import RedisTimelineStorage
import copy
import json
import logging
import warnings

logger = logging.getLogger(__name__)

MODULE_IS_DEPRECATED = """
Module stream_framework.feeds.aggregated_feed.notification_feed is deprecated.
Please use stream_framework.feeds.notification_feed module.

Class stream_framework.feeds.aggregated_feed.notification_feed.RedisNotificationFeed
is replaced by stream_framework.feeds.notification_feed.redis.RedisNotificationFeed
"""

warnings.warn(MODULE_IS_DEPRECATED, DeprecationWarning)


class NotificationFeed(AggregatedFeed):

    '''
    Similar to an aggregated feed, but:
    - doesnt use the activity storage (serializes everything into the timeline storage)
    - features denormalized counts
    - pubsub signals which you can subscribe to
    For now this is entirely tied to Redis
    '''
    #: notification feeds only need a small max length
    max_length = 99
    key_format = 'notification_feed:1:user:%(user_id)s'
    #: the format we use to denormalize the count
    count_format = 'notification_feed:1:user:%(user_id)s:count'
    #: the key used for locking
    lock_format = 'notification_feed:1:user:%s:lock'
    #: the main channel to publish
    pubsub_main_channel = 'juggernaut'

    timeline_serializer = NotificationSerializer
    activity_storage_class = None
    activity_serializer = None

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
        from stream_framework.storage.redis.connection import get_redis_connection
        self.redis = get_redis_connection()

    def add_many(self, activities, **kwargs):
        '''
        Similar to the AggregatedActivity.add_many
        The only difference is that it denormalizes a count of unseen activities
        '''
        with self.redis.lock(self.lock_key, timeout=2):
            current_activities = AggregatedFeed.add_many(
                self, activities, **kwargs)
            # denormalize the count
            self.denormalize_count()
            # return the current state of the notification feed
            return current_activities

    def get_denormalized_count(self):
        '''
        Returns the denormalized count stored in self.count_key
        '''
        result = self.redis.get(self.count_key) or 0
        result = int(result)
        return result

    def set_denormalized_count(self, count):
        '''
        Updates the denormalized count to count

        :param count: the count to update to
        '''
        self.redis.set(self.count_key, count)
        self.publish_count(count)

    def publish_count(self, count):
        '''
        Published the count via pubsub

        :param count: the count to publish
        '''
        count_dict = dict(unread_count=count, unseen_count=count)
        count_data = json.dumps(count_dict)
        data = {'channel': self.pubsub_key, 'data': count_data}
        encoded_data = json.dumps(data)
        self.redis.publish(self.pubsub_main_channel, encoded_data)

    def denormalize_count(self):
        '''
        Denormalize the number of unseen aggregated activities to the key
        defined in self.count_key
        '''
        # now count the number of unseen
        count = self.count_unseen()
        # and update the count if it changed
        stored_count = self.get_denormalized_count()
        if stored_count != count:
            self.set_denormalized_count(count)
        return count

    def count_unseen(self, aggregated_activities=None):
        '''
        Counts the number of aggregated activities which are unseen

        :param aggregated_activities: allows you to specify the aggregated
            activities for improved performance
        '''
        count = 0
        if aggregated_activities is None:
            aggregated_activities = self[:self.max_length]
        for aggregated in aggregated_activities:
            if not aggregated.is_seen():
                count += 1
        return count

    def mark_all(self, seen=True, read=None):
        '''
        Mark all the entries as seen or read

        :param seen: set seen_at
        :param read: set read_at
        '''
        with self.redis.lock(self.lock_key, timeout=10):
            # get the current aggregated activities
            aggregated_activities = self[:self.max_length]
            # create the update dict
            update_dict = {}

            for aggregated_activity in aggregated_activities:
                changed = False
                old_activity = copy.deepcopy(aggregated_activity)
                if seen is True and not aggregated_activity.is_seen():
                    aggregated_activity.update_seen_at()
                    changed = True
                if read is True and not aggregated_activity.is_read():
                    aggregated_activity.update_read_at()
                    changed = True

                if changed:
                    update_dict[old_activity] = aggregated_activity

            # send the diff to the storage layer
            new, deleted = [], []
            changed = update_dict.items()
            self._update_from_diff(new, changed, deleted)

        # denormalize the count
        self.denormalize_count()

        # return the new activities
        return aggregated_activities


class RedisNotificationFeed(NotificationFeed):
    timeline_storage_class = RedisTimelineStorage
