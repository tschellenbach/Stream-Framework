from feedly.feeds.base import UserBaseFeed
from feedly.tasks import fanout_operation, follow_many, unfollow_many
from feedly.utils import chunks
from feedly.utils.timing import timer
import logging

logger = logging.getLogger(__name__)


def add_operation(feed, activities, trim=True, batch_interface=None):
    '''
    Add the activities to the feed
    functions used in tasks need to be at the main level of the module
    '''
    t = timer()
    msg_format = 'running %s.add_many operation for %s activities batch interface %s and trim %s'
    logger.debug(msg_format, feed, len(activities), batch_interface, trim)
    feed.add_many(activities, batch_interface=batch_interface, trim=trim)
    logger.debug('add many operation took %s seconds', t.next())


def remove_operation(feed, activities, trim=True, batch_interface=None):
    '''
    Remove the activities from the feed
    functions used in tasks need to be at the main level of the module
    '''
    t = timer()
    msg_format = 'running %s.remove_many operation for %s activities batch interface %s'
    logger.debug(msg_format, feed, len(activities), batch_interface)
    feed.remove_many(activities, trim=trim, batch_interface=batch_interface)
    logger.debug('remove many operation took %s seconds', t.next())


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
    fanout_chunk_size = 100

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
        self._start_fanout(
            self.feed_classes,
            user_id,
            add_operation,
            activities=[activity],
            # Enable trimming to prevent infinite data storage :)
            trim=True
        )
        return

    def update_user_activities(self, activities):
        self.user_feed_class.insert_activities(activities)

    def update_user_activity(self, activity):
        self.user_feed_class.insert_activities([activity])

    def remove_user_activity(self, user_id, activity):
        '''
        Remove the activity and then fanout to user followers

        :param user_id: the id of the user
        :param activity: the activity which to add
        '''
        # The we can only remove this after the other tasks completed
        # TODO: clean up the activity after the fanout
        # self.user_feed_class.remove_activity(activity)

        user_feed = self.get_user_feed(user_id)
        user_feed.remove(activity)
        self._start_fanout(
            self.feed_classes,
            user_id,
            remove_operation,
            activities=[activity],
            # Enable trimming to prevent infinite data storage :)
            trim=True
        )
        return

    def follow_feed(self, feed, activities):
        '''
        copies source_feed entries into feed
        it will only copy follow_activity_limit activities

        :param feed: the feed to copy to
        :param activities: the activities to copy into the feed
        '''
        if activities:
            return feed.add_many(activities)

    def unfollow_feed(self, feed, source_feed):
        '''
        removes entries originating from the source feed form the feed class
        this will remove all activities, so this could take a wh
        :param feed: the feed to copy to
        :param source_feed: the feed with a list of activities to remove
        '''
        activities = source_feed[:]  # need to slice
        if activities:
            return feed.remove_many(activities)

    def follow_user(self, user_id, target_user_id, async=True):
        '''
        user_id starts following target_user_id

        :param user_id: the user which is doing the following/unfollowing
        :target_user_id: the user which is being unfollowed
        '''
        source_feed = self.get_user_feed(target_user_id)
        # fetch the activities only once
        activities = source_feed[:self.follow_activity_limit]
        for user_feed in self.get_feeds(user_id).values():
            self.follow_feed(user_feed, activities)

    def unfollow_user(self, user_id, target_user_id, async=True):
        '''
        unfollows the user

        :param user_id: the user which is doing the following/unfollowing
        :target_user_id: the user which is being unfollowed
        '''
        if async:
            unfollow_many_fn = unfollow_many.delay
        else:
            unfollow_many_fn = unfollow_many

        unfollow_many_fn(self, user_id, [target_user_id])

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
            self,
            user_id,
            target_ids,
            self.follow_activity_limit
        )

    def _start_fanout(self, feed_classes, user_id, operation, follower_ids=None, *args, **kwargs):
        '''
        Start fanout applies the given operation to the feeds of the users
        followers

        It takes the following ids and distributes them per fanout_chunk_size
        into smaller tasks

        :param feed_classes: the feed classes to run the operation on
        :param user_id: the user id to run the operation for
        :param operation: the operation function applied to all follower feeds
        :param follower_ids: (optionally) specify the list of followers
        :param args: args passed to the operation
        :param kwargs: kwargs passed to the operation
        '''
        user_ids = follower_ids or self.get_user_follower_ids(user_id=user_id)
        user_ids_chunks = list(chunks(user_ids, self.fanout_chunk_size))
        msg_format = 'spawning %s subtasks for %s user ids in chunks of %s users'
        logger.info(msg_format, len(user_ids_chunks),
                    len(user_ids), self.fanout_chunk_size)

        # now actually create the tasks
        subs = []
        for ids_chunk in user_ids_chunks:
            for name, feed_class in feed_classes.items():
                feed_class_dict = dict()
                feed_class_dict[name] = feed_class
                task_args = [
                    self, feed_class_dict, ids_chunk, operation] + list(args)
                sub = fanout_operation.apply_async(
                    args=task_args,
                    kwargs=kwargs
                )
                subs.append(sub)
        return subs

    def _fanout_task(self, user_ids, feed_classes, operation, *args, **kwargs):
        '''
        This functionality is called from within feedly.tasks.fanout_operation

        :param user_ids: the list of user ids which feeds we should apply the
        operation against
        :param feed_classes: the feed classes to change
        :param operation: the function to run on all the feeds
        :param args: args to pass to the operation
        :param kwargs: kwargs to pass to the operation
        '''
        separator = '===' * 10
        logger.info('%s starting fanout %s', separator, separator)
        for name, feed_class in feed_classes.items():
            batch_context_manager = feed_class.get_timeline_batch_interface()
            msg_format = 'starting batch interface for feed %s, fanning out to %s users'
            with batch_context_manager as batch_interface:
                logger.info(msg_format, name, len(user_ids))
                kwargs['batch_interface'] = batch_interface
                for user_id in user_ids:
                    logger.debug('now handling fanout to user %s', user_id)
                    feed = feed_class(user_id)
                    operation(feed, *args, **kwargs)
            logger.info('finished fanout for feed %s', name)

    def batch_import(self, user_id, activities, fanout=True, chunk_size=500):
        '''
        Batch import all of the users activities and distributes
        them to the users followers

        **Example**::

            activities = [long list of activities]
            feedly.batch_import(13, activities, 500)

        :param user_id: the user who created the activities
        :param activities: a list of activities from this user
        :param chunk_size: per how many activities to run the batch operations

        '''
        activities = list(activities)
        # skip empty lists
        if not activities:
            return
        logger.info('running batch import for user %s', user_id)
        follower_ids = self.get_user_follower_ids(user_id=user_id)
        logger.info('retrieved %s follower ids', len(follower_ids))
        user_feed = self.get_user_feed(user_id)
        if activities[0].actor_id != user_id:
            raise ValueError('Send activities for only one user please')

        activity_chunks = list(chunks(activities, chunk_size))
        logger.info('processing %s items in %s chunks of %s',
                    len(activities), len(activity_chunks), chunk_size)

        for index, activity_chunk in enumerate(activity_chunks):
            # first insert into the global activity storage
            self.user_feed_class.insert_activities(activity_chunk)
            logger.info(
                'inserted chunk %s (length %s) into the global activity store', index, len(activity_chunk))
            # next add the activities to the users personal timeline
            user_feed.add_many(activity_chunk)
            logger.info(
                'inserted chunk %s (length %s) into the user feed', index, len(activity_chunk))
            # now start a big fanout task
            if fanout:
                logger.info('starting task fanout for chunk %s', index)
                self._start_fanout(
                    self.feed_classes,
                    user_id,
                    add_operation,
                    follower_ids=follower_ids,
                    activities=activity_chunk,
                    # disable trimming during the import as its really really
                    # slow
                    trim=False
                )

    def flush(self):
        '''
        Flushes all the feeds
        '''
        # TODO why do we have this method?
        for name, feed_class in self.feed_classes.items():
            feed_class.flush()
        self.user_feed_class.flush()
