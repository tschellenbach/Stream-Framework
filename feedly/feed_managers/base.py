from feedly.utils import chunks
from feedly.tasks import fanout_operation
from feedly.tasks import follow_many
from feedly.feeds.base import UserBaseFeed


# functions used in tasks need to be at the main level of the module
def add_operation(feed, activities, batch_interface):
    feed.add_many(activities, batch_interface=batch_interface)


def remove_operation(feed, activities, batch_interface):
    feed.remove_many(activities, batch_interface=batch_interface)


class BaseFeedly(object):
    pass


class Feedly(BaseFeedly):
    follow_activity_limit = 5000
    fanout_chunk_size = 1000

    feed_classes = []
    user_feed_class = UserBaseFeed

    def __init__(self):
        '''
        This manager is built specifically for the love feed

        :feed_class the feed
        :user_feed_class where user activity gets stored (defaults to same as :feed_class param)

        '''
        pass

    def get_feeds(self, user_id):
        '''
        get the feed that contains the sum of all activity
        from feeds :user_id is subscribed to

        '''
        return [feed(user_id) for feed in self.feed_classes]

    def get_user_feed(self, user_id):
        '''
        feed where activity from :user_id is saved

        '''
        return self.user_feed_class(user_id)

    def add_user_activity(self, user_id, activity):
        '''
        Store the new activity and then fanout to user followers

        '''
        self.get_user_feed(user_id).insert_activity(activity)

        user_feed = self.get_user_feed(user_id)
        user_feed.add(activity)
        self._fanout(
            self.feed_classes,
            user_id,
            add_operation,
            activities=[activity]
        )
        return

    def remove_user_activity(self, user_id, activity):
        '''
        Remove the activity and then fanout to user followers

        '''
        self.feed_class.remove_activity(activity)
        user_feed = self.get_user_feed(user_id)
        user_feed.remove(activity)
        self._fanout(
            self.feed_classes,
            user_id,
            remove_operation,
            activities=[activity]
        )
        return

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
        target_feed = self.get_user_feed(target_user_id)
        for feed in self.get_feeds(user_id):
            self.unfollow_feed(feed, target_feed)

    def follow_user(self, user_id, target_user_id):
        '''
        user_id starts following target_user_id
        '''
        target_feed = self.get_user_feed(target_user_id)
        for user_feed in self.get_feeds(user_id):
            self.follow_feed(user_feed, target_feed)

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

    def _fanout(self, feed_classes, user_id, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per fanout_chunk_size
        '''
        user_ids = self.get_user_follower_ids(user_id)
        user_ids_chunks = chunks(user_ids, self.fanout_chunk_size)
        for ids_chunk in user_ids_chunks:
            fanout_operation.delay(
                self, feed_classes, ids_chunk, operation, *args, **kwargs
            )

    def _fanout_task(self, user_ids, feed_classes, operation, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        for feed_class in feed_classes:
            with feed_class.get_timeline_batch_interface() as batch_interface:

                kwargs['batch_interface'] = batch_interface
                for user_id in user_ids:
                    feed = feed_class(user_id)
                    operation(feed, *args, **kwargs)

    def flush(self):
        for feed_class in self.feed_classes:
            feed_class.flush()
        self.user_feed_class.flush()
