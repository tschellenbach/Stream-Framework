from stream_framework.activity import NotificationActivity
from stream_framework.aggregators.base import NotificationAggregator
from stream_framework.feeds.aggregated_feed.base import AggregatedFeed
from stream_framework.serializers.aggregated_activity_serializer import NotificationSerializer
from stream_framework.storage.base_lists_storage import BaseListsStorage

import logging
logger = logging.getLogger(__name__)


class BaseNotificationFeed(AggregatedFeed):
    '''
    Similar to an aggregated feed, but:
    - does not use the activity storage (serializes everything into the timeline storage)
    - tracks unseen/unread aggregated activities
    - enables counting of unseen/unread aggregated activities
    - enables marking of unseen/unread aggregated activities as seen/read
    '''

    key_format = 'notification_feed:%(user_id)s'

    timeline_serializer = NotificationSerializer
    aggregator_class = NotificationAggregator
    aggregated_activity_class = NotificationActivity
    activity_storage_class = None
    activity_serializer = None

    # : the storage class responsible to keep track of unseen/unread activity ids
    markers_storage_class = BaseListsStorage

    # : define whether or not to keep track of unseen activity ids
    track_unseen = True
    # : define whether or not to keep track of unread activity ids
    track_unread = True

    # : the max number of tracked unseen/unread activity ids
    markers_max_length = 100

    # : provides a part of the key used by markers_storage_class
    markers_key_format = 'notification_feed:%(user_id)s'

    #: the key used for distributed locking
    lock_format = 'notification_feed:%(user_id)s:lock'

    def __init__(self, user_id, **kwargs):
        super(BaseNotificationFeed, self).__init__(user_id, **kwargs)

        if self.markers_storage_class is None:
            if self.track_unread or self.track_unseen:
                raise ValueError('markers_storage_class must be set in case the unseen/unread activities are tracked')
        else:
            if not issubclass(self.markers_storage_class, BaseListsStorage):
                error_format = 'markers_storage_class attribute must be subclass of %s, encountered class %s'
                message = error_format % (BaseListsStorage, self.markers_storage_class)
                raise ValueError(message)

            markers_key = self.markers_key_format % {'user_id': user_id}
            self.feed_markers = self.markers_storage_class(key=markers_key,
                                                           max_length=self.markers_max_length)

    def count_unseen(self):
        '''
        Counts the number of aggregated activities which are unseen.
        '''
        if self.track_unseen:
            return self.feed_markers.count('unseen')

    def count_unread(self):
        '''
        Counts the number of aggregated activities which are unread.
        '''
        if self.track_unread:
            return self.feed_markers.count('unread')

    def get_notification_data(self):
        '''
        Provides custom notification data that is used by the transport layer
        when the feed is updated.
        '''
        notification_data = dict()

        if self.track_unseen and self.track_unread:
            unseen_count, unread_count = self.feed_markers.count('unseen', 'unread')
            notification_data['unseen_count'] = unseen_count
            notification_data['unread_count'] = unread_count
        elif self.track_unseen:
            unseen_count = self.feed_markers.count('unseen')
            notification_data['unseen_count'] = unseen_count
        elif self.track_unread:
            unread_count = self.feed_markers.count('unread')
            notification_data['unread_count'] = unread_count

        return notification_data

    def update_markers(self, unseen_ids=None, unread_ids=None, operation='add'):
        '''
        Starts or stops tracking aggregated activities as unseen and/or unread.
        '''
        if self.markers_storage_class is not None:
            if operation not in ('add', 'remove'):
                raise TypeError('%s is not supported' % operation)

            kwargs = dict()
            if unseen_ids is not None and self.track_unseen:
                kwargs['unseen'] = unseen_ids
            if unread_ids is not None and self.track_unread:
                kwargs['unread'] = unread_ids

            func = getattr(self.feed_markers, operation)
            func(**kwargs)

            # TODO use a real-time transport layer to notify for these updates

    def get_activity_slice(self, start=None, stop=None, rehydrate=True):
        '''
        Retrieves a slice of aggregated activities and annotates them as read and/or seen.
        '''
        activities = super(BaseNotificationFeed, self).get_activity_slice(start, stop, rehydrate)
        if activities and self.markers_storage_class is not None:

            if self.track_unseen and self.track_unread:
                unseen_ids, unread_ids = self.feed_markers.get('unseen', 'unread')
            elif self.track_unseen:
                unseen_ids = self.feed_markers.get('unseen')
            elif self.track_unread:
                unread_ids = self.feed_markers.get('unread')

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
        self.update_markers(ids, ids, operation='add')

    def remove_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Removes the activities from the notification feed and marks them as read/seen.
        '''
        super(BaseNotificationFeed, self).remove_many_aggregated(aggregated, *args, **kwargs)
        ids = [a.serialization_id for a in aggregated]
        self.update_markers(ids, ids, operation='remove')

    def mark_activity(self, activity_id, seen=True, read=False):
        '''
        Marks the given aggregated activity as seen or read or both.
        '''
        self.mark_activities([activity_id], seen, read)

    def mark_activities(self, activity_ids, seen=True, read=False):
        '''
        Marks all of the given aggregated activities as seen or read or both.
        '''
        unseen_ids = activity_ids if seen else []
        unread_ids = activity_ids if read else []
        self.update_markers(unseen_ids=unseen_ids,
                            unread_ids=unread_ids,
                            operation='remove')

    def mark_all(self, seen=True, read=False):
        '''
        Marks all of the feed's aggregated activities as seen or read or both.
        '''
        args = []
        if seen and self.track_unseen:
            args.append('unseen')
        if read and self.track_unread:
            args.append('unread')
        self.feed_markers.flush(*args)

    def delete(self):
        '''
        Deletes the feed and its markers.
        '''
        super(BaseNotificationFeed, self).delete()

        args = []
        if self.track_unseen:
            args.append('unseen')
        if self.track_unread:
            args.append('unread')
        self.feed_markers.flush(*args)
