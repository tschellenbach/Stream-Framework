from feedly.utils import chunks
from feedly.tasks import fanout_operation
from feedly.tasks import follow_many
from feedly.feeds.base import UserBaseFeed


def add_operation(feed, activities, batch_interface):
    '''
    Add the activities to the feed
    functions used in tasks need to be at the main level of the module
    '''
    feed.add_many(activities, batch_interface=batch_interface)


def remove_operation(feed, activities, batch_interface):
    '''
    Remove the activities from the feed
    functions used in tasks need to be at the main level of the module
    '''
    feed.remove_many(activities, batch_interface=batch_interface)


class BaseFeedly(object):
    pass


class Feedly(BaseFeedly):
    '''
    The Feedly class handles the fanout from a user's activity
    to all their follower's feeds
    
    .. note::
    
        Fanout is the process by which you get all the users which follow the user
        and spawn many asynchronous tasks which all push a bit of data
        to the feeds of these followers.
    
    See the :class:`.PinFeedly` class for an example implementation.
    
    You will definitely need to implement:
    
    - feed_classes
    - user_feed_class
    - get_user_follower_ids
    
    '''
    #: a dictionary with the feeds to fanout to
    #: for example feed_classes = dict(normal=PinFeed, aggregated=AggregatedPinFeed)
    feed_classes = {}
    #: the user feed class (it stores the latest activity by one user)
    user_feed_class = UserBaseFeed
    
    #: the number of activities which enter your feed when you follow someone
    follow_activity_limit = 5000
    #: the number of users which are handled in one asynchronous task
    #: when doing the fanout
    fanout_chunk_size = 1000

    def __init__(self):
        '''
        This manager is built specifically for the love feed

        :feed_class the feed
        :user_feed_class where user activity gets stored (defaults to same as :feed_class param)

        '''
        pass
    
    def get_user_follower_ids(self, user_id):
        '''
        returns the list of ids of user_id followers
        this depends on how you store followers/friends etc
        and is not implemented in feedly
        '''
        raise NotImplementedError()

    def get_feeds(self, user_id):
        '''
        get the feed that contains the sum of all activity
        from feeds :user_id is subscribed to
        
        :returns dict: a dictionary with the feeds we're pushing to
        '''
        return dict([(k, feed(user_id)) for k, feed in self.feed_classes.items()])

    def get_user_feed(self, user_id):
        '''
        feed where activity from :user_id is saved
        
        :param user_id: the id of the user
        '''
        return self.user_feed_class(user_id)

    def add_user_activity(self, user_id, activity):
        '''
        Store the new activity and then fanout to user followers
        
        This function will
        - store the activity in the activity storage
        - store it in the user feed (list of activities for one user)
        - fanout for all feed_classes

        :param user_id: the id of the user
        :param activity: the activity which to add
        '''
        self.user_feed_class.insert_activity(activity)
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

        :param user_id: the id of the user
        :param activity: the activity which to add
        '''
        self.user_feed_class.remove_activity(activity)

        user_feed = self.get_user_feed(user_id)
        user_feed.remove(activity)
        self._fanout(
            self.feed_classes,
            user_id,
            remove_operation,
            activities=[activity]
        )
        return

    def follow_feed(self, feed, source_feed):
        '''
        copies source_feed entries into feed
        it will only copy follow_activity_limit activities
        
        :param feed: the feed to copy to
        :param source_feed: the feed to copy from
        '''
        activities = source_feed[:self.follow_activity_limit]
        return feed.add_many(activities)

    def unfollow_feed(self, feed, source_feed):
        '''
        removes entries originating from the source feed form the feed class
        this will remove all activities, so this could take a while
        
        :param feed: the feed to copy to
        :param source_feed: the feed with a list of activities to remove
        '''
        activities = source_feed[:]  # need to slice
        return feed.remove_many(activities)
    
    def follow_user(self, user_id, target_user_id):
        '''
        user_id starts following target_user_id
        
        :param user_id: the user which is doing the following/unfollowing
        :target_user_id: the user which is being unfollowed
        '''
        source_feed = self.get_user_feed(target_user_id)
        for feed_name, user_feed in self.get_feeds(user_id).items():
            self.follow_feed(user_feed, source_feed)

    def unfollow_user(self, user_id, target_user_id):
        '''
        unfollows the user
        
        :param user_id: the user which is doing the following/unfollowing
        :target_user_id: the user which is being unfollowed
        '''
        source_feed = self.get_user_feed(target_user_id)
        for feed in self.get_feeds(user_id).values():
            self.unfollow_feed(feed, source_feed)

    def follow_many_users(self, user_id, target_ids, async=True):
        '''
        copies feeds for target_ids in user_id
        
        :param user_id: the user which is doing the following/unfollowing
        :param target_ids: the user to follow
        :param async: controls if the operation should be done via celery
        '''
        if async:
            follow_many_fn = follow_many.delay
        else:
            follow_many_fn = follow_many

        follow_many_fn(
            feeds=self.get_feeds(user_id).values(),
            target_feeds=map(self.get_user_feed, target_ids),
            follow_limit=self.follow_activity_limit
        )

    def _fanout(self, feed_classes, user_id, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per fanout_chunk_size
        '''
        user_ids = self.get_user_follower_ids(user_id=user_id)
        user_ids_chunks = chunks(user_ids, self.fanout_chunk_size)
        for ids_chunk in user_ids_chunks:
            fanout_operation(
                self, feed_classes, ids_chunk, operation, *args, **kwargs
            )

    def _fanout_task(self, user_ids, feed_classes, operation, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        for name, feed_class in feed_classes.items():
            with feed_class.get_timeline_batch_interface() as batch_interface:
                kwargs['batch_interface'] = batch_interface
                for user_id in user_ids:
                    feed = feed_class(user_id)
                    operation(feed, *args, **kwargs)

    def flush(self):
        '''
        Flushes all the feeds
        '''
        #TODO why do we have this method?
        for name, feed_class in self.feed_classes.items():
            feed_class.flush()
        self.user_feed_class.flush()
