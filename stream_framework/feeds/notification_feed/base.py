from stream_framework.activity import NotificationActivity
from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.serializers.aggregated_activity_serializer import NotificationSerializer
from stream_framework.storage.base_lists_storage import BaseListsStorage
from stream_framework.utils.validate import validate_type_strict

import logging
logger = logging.getLogger(__name__)


class BaseNotificationFeed(AggregatedFeed):

    key_format = 'notification_feed:%(user_id)s'

    timeline_serializer = NotificationSerializer
    aggregated_activity_class = NotificationActivity
    activity_storage_class = None
    activity_serializer = None

    # : the storage class responsible to keep track of unseen/unread activity ids
    counters_storage_class = None

    # : define whether or not to keep track of unseen activity ids
    track_unseen = True
    # : define whether or not to keep track of unread activity ids
    track_unread = True

    # : the max number of tracked unseen/unread activity ids
    counters_max_length = 100

    # : provides a part of the key used by counters_storage_class
    counters_key_format = 'notification_feed:%(user_id)s'

    #: the key used for distributed locking
    lock_format = 'notification_feed:%(user_id)s:lock'

    def __init__(self, user_id):
        super(BaseNotificationFeed, self).__init__(user_id)

        if self.counters_storage_class is None:
            if self.track_unread or self.track_unseen:
                raise ValueError('counters_storage_class must be set in case the unseen/unread activities are tracked')
        else:
            validate_type_strict(self.counters_storage_class, BaseListsStorage)
            counters_key = self.counters_key_format % {'user_id': user_id}
            self.feed_counters = self.counters_storage_class(key=counters_key,
                                                             max_length=self.counters_max_length)

    def get_notification_data(self):
        '''
        Provides custom notification data that is used by the transport layer
        when the feed is updated.
        '''
        notification_data = dict()

        if self.track_unseen and self.track_unread:
            unseen_count, unread_count = self.feed_counters.count('unseen', 'unread')
            notification_data['unseen_count'] = unseen_count
            notification_data['unread_count'] = unread_count
        elif self.track_unseen:
            unseen_count = self.feed_counters.count('unseen')
            notification_data['unseen_count'] = unseen_count
        elif self.track_unread:
            unread_count = self.feed_counters.count('unread')
            notification_data['unread_count'] = unread_count

        return notification_data

    def update_counters(self, unseen_ids=None, unread_ids=None, operation='add'):
        '''
        Starts or stops tracking activities as unseen and/or unread.
        '''
        if self.counters_storage_class is not None:
            if operation not in ('add', 'remove'):
                raise TypeError('%s is not supported' % operation)

            kwagrs = dict()
            if unseen_ids is not None and self.track_unseen:
                kwagrs['unseen'] = unseen_ids
            if unread_ids is not None and self.track_unread:
                kwagrs['unread'] = unread_ids

            func = getattr(self.feed_counters, operation)
            func(**kwagrs)

            # TODO fix this - in case an activity is added or removed the on_update_feed was already invoked
            # TODO use a real-time transport layer to notify for these updates
            self.on_update_feed([], [], self.get_notification_data())

    def get_activity_slice(self, start=None, stop=None, rehydrate=True):
        '''
        Retrieves a slice of activities and annotates them as read and/or seen.
        '''
        activities = super(BaseNotificationFeed, self).get_activity_slice(start, stop, rehydrate)
        if activities and self.counters_storage_class is not None:

            if self.track_unseen and self.track_unread:
                unseen_ids, unread_ids = self.feed_counters.get('unseen', 'unread')
            elif self.track_unseen:
                unseen_ids = self.feed_counters.get('unseen')
            elif self.track_unread:
                unread_ids = self.feed_counters.get('unread')

            for activity in activities:
                if self.track_unseen:
                    activity.is_seen = activity.serialization_id not in unseen_ids
                if self.track_unread:
                    activity.is_read = activity.serialization_id not in unread_ids

        return activities

    def add_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Adds the activities to the notification feed and marks them as unread/unseen.
        '''
        super(BaseNotificationFeed, self).add_many_aggregated(aggregated, *args, **kwargs)
        ids = [a.serialization_id for a in aggregated]
        self.update_counters(ids, ids, operation='add')

    def remove_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Removes the activities from the notification feed and marks them as read/seen.
        '''
        super(BaseNotificationFeed, self).remove_many_aggregated(aggregated, *args, **kwargs)
        ids = [a.serialization_id for a in aggregated]
        self.update_counters(ids, ids, operation='remove')

    def mark_activity(self, activity_id, seen=True, read=False):
        '''
        Marks the given activity as seen or read or both.
        '''
        self.mark_activities([activity_id], seen, read)

    def mark_activities(self, activity_ids, seen=True, read=False):
        '''
        Marks all of the given activities as seen or read or both.
        '''
        unseen_ids = activity_ids if seen else []
        unread_ids = activity_ids if read else []
        self.update_counters(unseen_ids=unseen_ids,
                             unread_ids=unread_ids,
                             operation='remove')

    def mark_all(self, seen=True, read=False):
        '''
        Marks all of the given activities as seen or read or both.
        '''
        args = []
        if seen and self.track_unseen:
            args.append('unseen')
        if read and self.track_unread:
            args.append('unread')
        self.feed_counters.flush(*args)
