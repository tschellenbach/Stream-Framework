from feedly.utils import chunks
from feedly.tasks import fanout_operation


# functions used in tasks need to be at the main level of the module
def add_operation(feed, activity_id):
    feed.add(activity_id)


def remove_operation(feed, activity_id):
    feed.remove(activity_id)


class Feedly(object):

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
            'feed_%(user_id)s',
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def get_user_feed(self, user_id):
        '''
        feed where activity from :user_id is saved

        '''
        return self.feed_class(
            user_id,
            'user_%(user_id)s_feed',
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def add_user_activity(self, user_id, activity):
        '''
        Store the new activity and then fanout to user followers

        This is really write intensive
        Reads are super light though
        '''

        self.feed_class.insert_activity(
            activity,
            **self.activity_storage_options
        )
        self.get_user_feed(user_id)\
            .add(activity.serialization_id)
        feeds = self._fanout(
            user_id,
            add_operation,
            activity_id=activity.serialization_id
        )
        return feeds

    def follow_feed(self, feed, target_feed):
        activities = feed[:self.follow_activity_limit]
        return target_feed.add_many(activities)

    def unfollow_feed(self, feed, target_feed):
        activities = feed[:] # need to slice
        return target_feed.remove_many(activities)

    def unfollow_user(self, user_id, target_user_id):
        feed = self.get_feed(user_id)
        target_feed = self.get_user_feed(target_user_id)
        return self.unfollow_feed(feed, target_feed)

    def follow_user(self, user_id, target_user_id):
        feed = self.get_feed(user_id)
        target_feed = self.get_user_feed(target_user_id)
        return self.follow_feed(feed, target_feed)

    def get_user_follower_ids(self, user_id):
        '''
        returns the list of ids of user_id followers

        '''
        raise NotImplementedError()

    def get_follower_feeds(self, user_id):
        follower_ids = self.get_user_follower_ids(user_id)
        feeds = map(self.get_feed, follower_ids)
        return feeds

    def _fanout(self, user_id, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per fanout_chunk_size
        '''
        follower_feeds = self.get_follower_feeds(user_id)
        follower_feeds_chunks = chunks(follower_feeds, self.fanout_chunk_size)
        for feeds_chunk in follower_feeds_chunks:
            fanout_operation(
                self, feeds_chunk, operation, *args, **kwargs
            )

    def _fanout_task(self, feeds, operation, max_length=None, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''

        for feed in feeds:
            operation(feed, *args, **kwargs)
