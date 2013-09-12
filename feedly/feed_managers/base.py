from feedly.feeds.base import UserBaseFeed
from feedly.tasks import fanout_operation, follow_many, unfollow_many
from feedly.utils import chunks
from feedly.utils.timing import timer
import logging
from feedly.feeds.redis import RedisFeed

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


class Feedly(object):

    '''
    The Feedly class handles the fanout from a user's activity
    to all their follower's feeds

    .. note::

        Fanout is the process which pushes a little bit of data to all of your
        followers in many small and asynchronous tasks.

    To write your own Feedly class you will need to implement

    - get_user_follower_ids
    - feed_classes
    - user_feed_class
    
    **Example** ::
        
        from feedly.feed_managers.base import Feedly
        
        class PinFeedly(Feedly):
            # customize the feed classes we write to
            feed_classes = dict(
                normal=PinFeed,
                aggregated=AggregatedPinFeed
            )
            # customize the user feed class
            user_feed_class = UserPinFeed
            
            # define how feedly can get the follower ids
            def get_user_follower_ids(self, user_id):
                return Follow.objects.filter(target=user_id).values_list('user_id', flat=True)
          
            # utility functions to easy integration for your project
            def add_pin(self, pin):
                activity = pin.create_activity()
                # add user activity adds it to the user feed, and starts the fanout
                self.add_user_activity(pin.user_id, activity)
        
            def remove_pin(self, pin):
                activity = pin.create_activity()
                # removes the pin from the user's followers feeds
                self.remove_user_activity(pin.user_id, activity)

    '''
    # : a dictionary with the feeds to fanout to
    # : for example feed_classes = dict(normal=PinFeed, aggregated=AggregatedPinFeed)
    feed_classes = dict(
        normal=RedisFeed
    )
    # : the user feed class (it stores the latest activity by one user)
    user_feed_class = UserBaseFeed

    # : the number of activities which enter your feed when you follow someone
    follow_activity_limit = 5000
    # : the number of users which are handled in one asynchronous task
    # : when doing the fanout
    fanout_chunk_size = 100

    def __init__(self):
        pass

    def get_user_follower_ids(self, user_id):
        '''
        Returns a list of users ids which follow the given user
        
        :param user_id: the user id for which to get the follower ids
        '''
        raise NotImplementedError()

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
        # add into the global activity cache (if we are using it)
        self.user_feed_class.insert_activity(activity)
        # now add to the user's personal feed
        user_feed = self.get_user_feed(user_id)
        user_feed.add(activity)
        # lookup the followers
        follower_ids = self.get_user_follower_ids(user_id=user_id)
        # create the fanout tasks
        for feed_class in self.feed_classes.values():
            # operation specific arguments
            # enable trimming to prevent infinite data storage :)
            operation_kwargs = dict(activities=[activity], trim=True)
            self.create_fanout_tasks(
                follower_ids,
                feed_class,
                add_operation,
                operation_kwargs=operation_kwargs
            )
        return

    def remove_user_activity(self, user_id, activity):
        '''
        Remove the activity and then fanout to user followers

        :param user_id: the id of the user
        :param activity: the activity which to add
        '''
        # we don't remove from the global feed due to race conditions
        # but we do remove from the personal feed
        user_feed = self.get_user_feed(user_id)
        user_feed.remove(activity)

        # no need to trim when removing items
        operation_kwargs = dict(activities=[activity], trim=False)

        # lookup the followers to remove the activity from
        follower_ids = self.get_user_follower_ids(user_id=user_id)

        # create the fanout tasks
        for feed_class in self.feed_classes.values():
            self.create_fanout_tasks(
                follower_ids,
                feed_class,
                remove_operation,
                operation_kwargs=operation_kwargs
            )
        return

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

    def update_user_activities(self, activities):
        '''
        Update the user activities
        :param activities: the activities to update
        '''
        self.user_feed_class.insert_activities(activities)

    def update_user_activity(self, activity):
        self.update_user_activities([activity])

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

    def create_fanout_tasks(self, follower_ids, feed_class, operation, operation_kwargs=None):
        '''
        Creates the fanout task for the given activities and feed classes
        followers

        It takes the following ids and distributes them per fanout_chunk_size
        into smaller tasks

        :param follower_ids: specify the list of followers
        :param feed_class: the feed classes to run the operation on
        :param operation: the operation function applied to all follower feeds
        :param operation_kwargs: kwargs passed to the operation
        '''
        chunk_size = self.fanout_chunk_size
        user_ids_chunks = list(chunks(follower_ids, chunk_size))
        msg_format = 'spawning %s subtasks for %s user ids in chunks of %s users'
        logger.info(
            msg_format, len(user_ids_chunks), len(follower_ids), chunk_size)

        tasks = []
        # now actually create the tasks
        for ids_chunk in user_ids_chunks:
            task = fanout_operation.delay(
                feed_manager=self,
                feed_class=feed_class,
                user_ids=ids_chunk,
                operation=operation,
                operation_kwargs=operation_kwargs
            )
            tasks.append(task)
        return tasks

    def fanout(self, user_ids, feed_class, operation, operation_kwargs):
        '''
        This functionality is called from within feedly.tasks.fanout_operation

        :param user_ids: the list of user ids which feeds we should apply the
        operation against
        :param feed_class: the feed to run the operation on
        :param operation: the operation to run on the feed
        :param operation_kwargs: kwargs to pass to the operation

        '''
        separator = '===' * 10
        logger.info('%s starting fanout %s', separator, separator)
        batch_context_manager = feed_class.get_timeline_batch_interface()
        msg_format = 'starting batch interface for feed %s, fanning out to %s users'
        with batch_context_manager as batch_interface:
            logger.info(msg_format, feed_class, len(user_ids))
            operation_kwargs['batch_interface'] = batch_interface
            for user_id in user_ids:
                logger.debug('now handling fanout to user %s', user_id)
                feed = feed_class(user_id)
                operation(feed, **operation_kwargs)
        logger.info('finished fanout for feed %s', feed_class)

    def batch_import(self, user_id, activities, fanout=True, chunk_size=500):
        '''
        Batch import all of the users activities and distributes
        them to the users followers

        **Example**::

            activities = [long list of activities]
            feedly.batch_import(13, activities, 500)

        :param user_id: the user who created the activities
        :param activities: a list of activities from this user
        :param fanout: if we should run the fanout or not
        :param chunk_size: per how many activities to run the batch operations

        '''
        activities = list(activities)
        # skip empty lists
        if not activities:
            return
        logger.info('running batch import for user %s', user_id)

        # lookup the follower ids if we need them later
        follower_ids = []
        if fanout:
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
            user_feed.add_many(activity_chunk, trim=False)
            logger.info(
                'inserted chunk %s (length %s) into the user feed', index, len(activity_chunk))
            # now start a big fanout task
            if fanout:
                logger.info('starting task fanout for chunk %s', index)

                # create the fanout tasks
                operation_kwargs = dict(activities=activity_chunk, trim=False)
                for feed_class in self.feed_classes.values():
                    self.create_fanout_tasks(
                        follower_ids,
                        feed_class,
                        add_operation,
                        operation_kwargs=operation_kwargs
                    )
