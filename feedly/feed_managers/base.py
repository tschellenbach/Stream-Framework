from feedly.utils import chunks
from feedly.tasks import fanout_operation
from feedly.tasks import follow_many


# functions used in tasks need to be at the main level of the module
def add_operation(feed_class, feed_keys, activities, timeline_storage_options):
    feed_class.timeline_fanout_add(feed_keys, activities, timeline_storage_options=timeline_storage_options)

def remove_operation(feed_class, feed_keys, activities, timeline_storage_options):
    feed_class.timeline_fanout_remove(feed_keys, activities, timeline_storage_options=timeline_storage_options)


class Feedly(object):

    feed_key_format = 'feed_%(user_id)s'
    user_feed_key_format = 'user_%(user_id)s_feed'

    def __init__(self, feed_class, timeline_storage_options={}, activity_storage_options={}, follow_activity_limit=5000, fanout_chunk_size=1000):
        '''
        This manager is built specifically for the love feed
        '''
        self.feed_class = feed_class
        self.timeline_storage_options = timeline_storage_options.copy()
        self.activity_storage_options = activity_storage_options.copy()
        self.follow_activity_limit = follow_activity_limit
        self.fanout_chunk_size = fanout_chunk_size

    def get_feed(self, user_id):
        '''
        get the feed that contains the sum of all activity
        from feeds :user_id is subscribed to

        '''
        return self.feed_class(
            user_id,
            self.feed_key_format,
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def get_user_feed(self, user_id):
        '''
        feed where activity from :user_id is saved

        '''
        return self.feed_class(
            user_id,
            self.user_feed_key_format,
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def add_user_activity(self, user_id, activity):
        '''
        Store the new activity and then fanout to user followers

        '''

        activity_id = activity.serialization_id
        self.feed_class.insert_activity(
            activity,
            **self.activity_storage_options
        )
        self.get_user_feed(user_id)\
            .add(activity_id)
        feeds = self._fanout(
            user_id,
            add_operation,
            activities=[activity_id],
            timeline_storage_options=self.timeline_storage_options
        )
        return feeds

    def remove_user_activity(self, user_id, activity):
        '''
        Remove the activity and then fanout to user followers

        '''
        activity_id = activity.serialization_id
        self.feed_class.remove_activity(
            activity,
            **self.activity_storage_options
        )
        self.get_user_feed(user_id)\
            .remove(activity_id)
        feeds = self._fanout(
            user_id,
            remove_operation,
            activities=[activity_id],
            timeline_storage_options=self.timeline_storage_options
        )
        return feeds

    def follow_feed(self, feed, target_feed):
        '''
        copies target_feed entries in feed
        '''
        activities = target_feed[:self.follow_activity_limit]
        activity_ids = [a.serialization_id for a in activities]
        return feed.add_many(activity_ids)

    def unfollow_feed(self, feed, target_feed):
        '''
        removes entries in target_feed from feed

        '''
        activities = feed[:] # need to slice
        activity_ids = [a.serialization_id for a in activities]
        return feed.remove_many(activity_ids)

    def unfollow_user(self, user_id, target_user_id):
        '''
        user_id stops following target_user_id

        '''
        feed = self.get_feed(user_id)
        target_feed = self.get_user_feed(target_user_id)
        return self.unfollow_feed(feed, target_feed)

    def follow_user(self, user_id, target_user_id):
        '''
        user_id starts following target_user_id
        '''
        feed = self.get_feed(user_id)
        target_feed = self.get_user_feed(target_user_id)
        return self.follow_feed(feed, target_feed)

    def follow_many_users(self, user_id, target_ids, async=True):
        '''
        copies feeds for target_ids in user_id 
        :async controls if the operation should be done via celery

        '''
        if async:
            follow_many_fn = follow_many.delay
        else:
            follow_many_fn = follow_many

        follow_many_fn(
            feed=self.get_feed(user_id),
            target_feeds=map(self.get_user_feed, target_ids),
            follow_limit=self.follow_activity_limit
        )

    def get_user_follower_ids(self, user_id):
        '''
        returns the list of ids of user_id followers

        '''
        raise NotImplementedError()

    def _fanout(self, user_id, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per fanout_chunk_size
        '''
        user_ids = self.get_user_follower_ids(user_id)
        user_ids_chunks = chunks(user_ids, self.fanout_chunk_size)

        for ids_chunk in user_ids_chunks:
            feed_keys = map(lambda i: self.feed_key_format % {'user_id': i}, ids_chunk)
            fanout_operation.delay(
                self, self.feed_class, feed_keys, operation, *args, **kwargs
            )

    def _fanout_task(self, feed_class, feed_keys, operation, max_length=None, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        operation(feed_class, feed_keys, *args, **kwargs)

    def flush(self):
        self.get_feed(None).flush()
        self.get_user_feed(None).flush()
