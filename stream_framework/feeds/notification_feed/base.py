from stream_framework.activity import NotificationActivity
from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.serializers.aggregated_activity_serializer import NotificationSerializer

import random
import logging
logger = logging.getLogger(__name__)


class BaseIdStorageClass(object):

    def set(self, ids):
        raise NotImplementedError()

    def add(self, ids):
        raise NotImplementedError()

    def remove(self, ids):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()


class NotificationFeed(AggregatedFeed):

    key_format = 'notification_feed:%(user_id)s'

    timeline_serializer = NotificationSerializer
    aggregated_activity_class = NotificationActivity
    activity_storage_class = None
    activity_serializer = None

    # : an optional storage used to keep track of unseen activity ids
    unseen_ids_storage_class = None
    # : an optional storage used to keep track of unread activity ids
    unread_ids_storage_class = None

    # : the max number of tracked unseen/unread activity ids
    unseen_unread_max_length = 100

    # : the chance to reduce the number of tracked unseen/unread activity ids
    unseen_unread_trim_chance = 0.1

    #: the key used for distributed locking
    lock_format = 'notification_feed:%(user_id)s:lock'

    def __init__(self, user_id):
        super(NotificationFeed, self).__init__(user_id)

        # TODO add validation that the storage classes inherit from BaseIdStorageClass
        if self.unseen_ids_storage_class:
            self.unseen_ids_storage = self.unseen_ids_storage_class()
        if self.unread_ids_storage_class:
            self.unread_ids_storage = self.unread_ids_storage_class()

    def trim_unseen_unread_ids(self):
        # trim the unseen/unread ids from time to time
        if random.random() <= self.unseen_unread_trim_chance:
            unseen_ids, unread_ids = self.get_unseen_unread_ids()
            unseen_ids_to_remove, unread_ids_to_remove = None, None

            if len(unseen_ids) > self.unseen_unread_max_length:
                unseen_ids_to_remove = sorted(unseen_ids, reverse=True)[self.unseen_unread_max_length:]
            if len(unread_ids) > self.unseen_unread_max_length:
                unread_ids_to_remove = sorted(unread_ids, reverse=True)[self.unseen_unread_max_length:]

            if unseen_ids_to_remove or unread_ids_to_remove:
                self.update_unseen_unread_ids(unseen_ids=unseen_ids_to_remove,
                                              unread_ids=unread_ids_to_remove,
                                              operation='remove')

    def update_unseen_unread_ids(self, unseen_ids=None, unread_ids=None, operation='set'):
        if operation is ('set', 'add', 'remove'):
            raise TypeError('%s is not supported' % operation)

        # TODO perform the operation in a transaction
        if self.unseen_ids_storage_class and unseen_ids:
            func = getattr(self.unseen_ids_storage, operation)
            func(unseen_ids)
        if self.unread_ids_storage_class and unread_ids:
            func = getattr(self.unread_ids_storage, operation)
            func(unread_ids)

        if operation == 'add':
            self.trim_unseen_unread_ids()

        # TODO fix this - in case an activity is added or removed the on_update_feed was already invoked
        # TODO use a real-time transport layer to notify for these updates
        self.on_update_feed([], [], self.get_notification_data())

    def get_unseen_unread_ids(self):
        '''
        Returns two lists with activity ids.
        The first one consists of ids of these aggregated activities that are not seen by the feed owner.
        The second one consists of ids of these aggregated activities that are not read.
        '''
        unseen_ids = []
        unread_ids = []

        # TODO retrieve them in a batch
        if self.unseen_ids_storage_class:
            unseen_ids = list(self.unseen_ids_storage)
        if self.unread_ids_storage_class:
            unread_ids = list(self.unread_ids_storage)

        return unseen_ids, unread_ids

    def count_unseen_unread_ids(self):
        '''
        Counts the number of aggregated activities which are unseen and/or unread
        '''
        unseen_ids, unread_ids = self.get_unseen_unread_ids()
        unseen_count = min(len(unseen_ids), self.unseen_unread_max_length)
        unread_count = min(len(unread_ids), self.unseen_unread_max_length)
        return unseen_count, unread_count

    def acquire_lock(self, timeout=None):
        '''
        Provides a locking mechanism based on Redis that works within a distributed environment.

        This method may be overridden in order to switch to a locking mechanism
        provided by an alternative to Redis software like ZooKeeper.
        '''
        if not hasattr(self, 'lock_key'):
            self.lock_key = self.lock_format % {'user_id': self.user_id}

            from stream_framework.storage.redis.connection import get_redis_connection
            self.redis = get_redis_connection()

        return self.redis.lock(self.lock_key, timeout=timeout)

    def get_activity_slice(self, start=None, stop=None, rehydrate=True):
        activities = super(NotificationFeed, self).get_activity_slice(start, stop, rehydrate)
        if activities and (self.unread_ids_storage_class or self.unseen_ids_storage):
            unseen_ids, unread_ids = self.get_unseen_unread_ids()
            for activity in activities:
                if self.unread_ids_storage_class:
                    activity.is_read = activity.serialization_id not in unread_ids
                if self.unseen_ids_storage_class:
                    activity.is_seen = activity.serialization_id not in unseen_ids
        return activities

    # TODO check whether remove_many needs to be overriden as well
    def add_many(self, activities, **kwargs):
        with self.acquire_lock(timeout=2):
            current_activities = super(NotificationFeed, self).add_many(activities, **kwargs)
            ids = [a.serialization_id for a in current_activities]
            # TODO this looks correct, right?
            self.update_unseen_unread_ids(ids, ids, operation='set')
            return current_activities

    def add_many_aggregated(self, aggregated, *args, **kwargs):
        super(NotificationFeed, self).add_many_aggregated(aggregated, *args, **kwargs)
        ids = [a.serialization_id for a in aggregated]
        self.update_unseen_unread_ids(ids, ids, operation='add')

    def remove_many_aggregated(self, aggregated, *args, **kwargs):
        super(NotificationFeed, self).remove_many_aggregated(aggregated, *args, **kwargs)
        ids = [a.serialization_id for a in aggregated]
        self.update_unseen_unread_ids(ids, ids, operation='remove')

    def get_notification_data(self):
        notification_data = dict()
        unseen_count, unread_count = self.count_unseen_unread_ids()

        if self.unseen_ids_storage_class:
            notification_data['unseen_count'] = unseen_count
        if self.unread_ids_storage_class:
            notification_data['unread_count'] = unread_count

        return notification_data

    def mark_activity(self, activity_id, seen=True, read=False):
        self.mark_activities([activity_id], seen, read)

    def mark_activities(self, activity_ids, seen=True, read=False):
        unseen_ids = activity_ids if seen else []
        unread_ids = activity_ids if read else []
        self.update_unseen_unread_ids(unseen_ids=unseen_ids,
                                      unread_ids=unread_ids,
                                      operation='remove')

    def mark_all(self, seen=True, read=False):
        '''
        Mark all the entries as seen or read
        '''
        self.update_unseen_unread_ids(unseen=[], unread=[], operation='set')
