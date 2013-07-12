from feedly.utils import chunks
from feedly.tasks import fanout_operation
from feedly.tasks import follow_many


# functions used in tasks need to be at the main level of the module
def add_operation(feed, activities, batch_interface):
    feed.add_many(activities, batch_interface=batch_interface)


def remove_operation(feed, activities, batch_interface):
    feed.remove_many(activities, batch_interface=batch_interface)


class Feedly(object):

    feed_key_format = 'feed_%(user_id)s'
    user_feed_key_format = 'user_%(user_id)s_feed'

    def __init__(self, feed_class, user_feed_class=None, timeline_storage_options={}, activity_storage_options={}, follow_activity_limit=5000, fanout_chunk_size=1000):
        '''
        This manager is built specifically for the love feed

        :feed_class the feed
        :user_feed_class where user activity gets stored (defaults to same as :feed_class param)
        :timeline_storage_options the options for the timeline storage
        :activity_storage_options the options for the activity storage

        '''
        self.feed_class = feed_class
        if user_feed_class is None:
            self.user_feed_class = feed_class
        else:
            self.user_feed_class = user_feed_class
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
        return self.user_feed_class(
            user_id,
            self.user_feed_key_format,
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def add_user_activity(self, user_id, activity):
        '''
        Store the new activity and then fanout to user followers

        '''
        self.feed_class.insert_activity(
            activity,
            **self.activity_storage_options
        )
        self.get_user_feed(user_id)\
            .add(activity)
        feeds = self._fanout(
            user_id,
            add_operation,
            activities=[activity]
        )
        return feeds

    def remove_user_activity(self, user_id, activity):
        '''
        Remove the activity and then fanout to user followers

        '''
        self.feed_class.remove_activity(
            activity,
            **self.activity_storage_options
        )
        self.get_user_feed(user_id)\
            .remove(activity)
        feeds = self._fanout(
            user_id,
            remove_operation,
            activities=[activity]
        )
        return feeds

    def follow_feed(self, feed, target_feed):
        '''
        copies target_feed entries in feed
        '''
        activities = target_feed[:self.follow_activity_limit]
        return feed.add_many(activities)

    def unfollow_feed(self, feed, target_feed):
        '''
        removes entries in target_feed from feed

        '''
        activities = feed[:]  # need to slice
        return feed.remove_many(activities)

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
            #TODO add back the .delay
            fanout_operation(
                self, ids_chunk, operation, *args, **kwargs
            )

    def _fanout_task(self, user_ids, operation, max_length=None, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        # TODO implement get_timeline_batch_interface as a class method
        with self.get_feed(None).get_timeline_batch_interface() as batch_interface:
            kwargs['batch_interface'] = batch_interface
            for feed in map(self.get_feed, user_ids):
                operation(feed, *args, **kwargs)

    def flush(self):
        # TODO add classmethods
        self.get_feed(None).flush()
        self.get_user_feed(None).flush()

