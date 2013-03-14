from django.contrib.auth.models import User
from feedly import get_redis_connection
from feedly.feed_managers.base import Feedly
from feedly.marker import FeedEndMarker
from feedly.utils import chunks
import logging
import datetime
from django.core.cache import cache


logger = logging.getLogger(__name__)


# functions used in tasks need to be at the main level of the module
def add_operation(feed, activity):
    feed.add(activity)


def remove_operation(feed, activity):
    feed.remove(activity)


class LoveFeedly(Feedly):
    '''
    The goal is to have super light reads.
    We don't really worry too much about the writes.

    However we try to keep them realtime by
    - writing to logged in user's feeds first

    In addition we reduce the storage requirements by
    - only storing the full feed for active users
    '''
    # When you follow someone the number of loves we add
    MAX_FOLLOW_LOVES = 24 * 20
    # The size of the chunks for doing a fanout
    FANOUT_CHUNK_SIZE = 10000

    def __init__(self, *args, **kwargs):
        '''
        This manager is built specifically for the love feed
        '''
        from feedly.feeds.love_feed import LoveFeed
        self.feed_class = LoveFeed

    def add_love(self, love):
        '''
        Fanout to all your followers

        This is really write intensive
        Reads are super light though
        '''
        activity = self.create_love_activity(love)

        feeds = self._fanout(love.user, add_operation, activity=activity)
        return feeds

    def remove_love(self, love):
        '''
        Fanout to all your followers

        This is really write intensive
        Reads are super light though
        '''
        activity = self.create_love_activity(love)
        feeds = self._fanout(love.user, remove_operation, activity=activity)
        return feeds

    def follow(self, follow):
        '''
        Gets the last loves of the target user
        up to MAX_FOLLOW_LOVES (currently set to 500)
        Subsequently add these to the feed in place
        Using redis.zadd

        So if N is the length of the feed
        And L is the number of new loves
        This operation will take
        L*Log(N)
        '''
        feed = self.feed_class(follow.user_id)
        target_loves = follow.target.get_profile(
        ).loves()[:self.MAX_FOLLOW_LOVES]
        activities = []
        for love in target_loves:
            activity = self.create_love_activity(love)
            activities.append(activity)
        feed.add_many(activities)
        return feed

    def follow_many(self, follows, max_loves=None, async=True):
        '''
        More efficient implementation for follows.
        The database query can be quite heavy though

        we do
        L = max(len(follows) * self.MAX_FOLLOW_LOVES, feed.max_length)
        operations

        This will take
        L*Log(N)
        Plus the time spend in the db

        If async=True this function will run in the background
        '''
        from feedly.tasks import follow_many
        feed = None
        if follows:
            follow = follows[0]
            user_id = follow.user_id
            followed_user_ids = [f.target_id for f in follows]
            follow_many_callable = follow_many.delay if async else follow_many
            feed = follow_many_callable(
                self, user_id, followed_user_ids, max_loves=max_loves)
        return feed

    def _follow_many_task(self, user_id, followed_user_ids, max_loves=None):
        '''
        Queries the database and performs the add many!
        This function is usually called via a task
        '''
        from entity.models import Love
        feed = self.feed_class(user_id)

        # determine the default max loves
        default_max_loves = max(
            len(followed_user_ids) * self.MAX_FOLLOW_LOVES, feed.max_length)

        # determine how many loves to select
        if max_loves is None:
            love_limit = default_max_loves
        else:
            love_limit = max_loves

        # create a list with all the activities
        loves = Love.objects.filter(user__in=followed_user_ids)
        loves = loves.order_by('-id')[:love_limit]
        activities = []
        for love in loves:
            activity = self.create_love_activity(love)
            activities.append(activity)

        logger.info('adding %s activities to feed %s', len(
            activities), feed.get_key())
        # actually add the activities to Redis
        feed.add_many(activities)

        # a custom max loves means our feed might be out of sync with the db
        # so we need to trim to remove the FeedEndMarker
        if max_loves is not None and max_loves < default_max_loves:
            feed.trim(max_loves)

        return feed

    def unfollow(self, follow):
        '''
        Delegates to unfollow_many
        '''
        follows = [follow]
        feed = self.unfollow_many(follows)
        return feed

    def unfollow_many(self, follows):
        '''
        Loop through the feed and remove the loves coming from follow.target_id

        This is using redis.zrem
        So if N is the length of the feed
        And L is the number of loves to remove
        L*log(N)

        Plus the intial lookup using zrange
        Which is N
        So N + L*Log(N) in total
        '''
        if follows:
            follow = follows[0]
            feed = self.feed_class(follow.user_id)
            target_ids = dict.fromkeys([f.target_id for f in follows])
            activities = feed[:feed.max_length]
            to_remove = []
            for activity in activities:
                if isinstance(activity, FeedEndMarker):
                    continue
                if activity.actor_id in target_ids:
                    to_remove.append(activity)
            feed.remove_many(to_remove)
        return feed

    def create_love_activity(self, love):
        '''
        Store a love in an activity object
        '''
        activity = love.create_activity()
        return activity

    def get_follower_ids(self, user):
        '''
        Wrapper for retrieving all the followers for a user
        '''
        profile = user.get_profile()
        following_ids = profile.cached_follower_ids()

        return following_ids

    def get_active_follower_ids(self, user, update_cache=False):
        '''
        Wrapper for retrieving all the active followers for a user
        '''
        key = 'active_follower_ids_%s' % user.id

        following_ids = cache.get(key)
        if following_ids is None or update_cache:
            last_two_weeks = datetime.datetime.today(
            ) - datetime.timedelta(days=7 * 2)
            profile = user.get_profile()
            following_ids = profile.follower_ids(
            ).filter(user__last_login__gte=last_two_weeks)
            following_ids = list(following_ids)
            cache.set(key, following_ids, 60 * 5)

        return following_ids

    def get_inactive_follower_ids(self, user, update_cache=False):
        '''
        Wrapper for retrieving all the inactive followers for a user
        '''
        key = 'inactive_follower_ids_%s' % user.id
        following_ids = cache.get(key)

        if following_ids is None or update_cache:
            last_two_weeks = datetime.datetime.today(
            ) - datetime.timedelta(days=7 * 2)
            profile = user.get_profile()
            following_ids = profile.follower_ids(
            ).filter(user__last_login__lt=last_two_weeks)
            following_ids = list(following_ids)
            cache.set(key, following_ids, 60 * 5)

        return following_ids

    def get_follower_groups(self, user, update_cache=False):
        '''
        Gets the active and inactive follower groups together with their
        feed max length
        '''
        from feedly.feeds.love_feed import INACTIVE_USER_MAX_LENGTH, ACTIVE_USER_MAX_LENGTH

        active_follower_ids = self.get_active_follower_ids(
            user, update_cache=update_cache)
        inactive_follower_ids = self.get_inactive_follower_ids(
            user, update_cache=update_cache)

        follower_ids = active_follower_ids + inactive_follower_ids

        active_follower_groups = list(
            chunks(active_follower_ids, self.FANOUT_CHUNK_SIZE))
        active_follower_groups = [(follower_group, ACTIVE_USER_MAX_LENGTH) for follower_group in active_follower_groups]

        inactive_follower_groups = list(
            chunks(inactive_follower_ids, self.FANOUT_CHUNK_SIZE))
        inactive_follower_groups = [(follower_group, INACTIVE_USER_MAX_LENGTH) for follower_group in inactive_follower_groups]

        follower_groups = active_follower_groups + inactive_follower_groups

        logger.info('divided %s fanouts into %s tasks', len(
            follower_ids), len(follower_groups))
        return follower_groups

    def _fanout(self, user, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per FANOUT_CHUNKS
        '''
        follower_groups = self.get_follower_groups(user)
        feeds = []
        for (follower_group, max_length) in follower_groups:
            # now, for these items pipeline/thread away via an async task
            from feedly.tasks import fanout_love
            fanout_love.delay(
                self, user, follower_group, operation,
                max_length=max_length, *args, **kwargs
            )

        # reset the feeds to get out of the distributed mode
        connection = get_redis_connection()
        for feed in feeds:
            feed.redis = connection

        return feeds

    def _fanout_task(self, user, following_group, operation, max_length=None, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        from feedly.feeds.love_feed import DatabaseFallbackLoveFeed
        connection = get_redis_connection()
        feed_class = DatabaseFallbackLoveFeed
        feeds = []

        # set the default to 24 * 150
        if max_length is None:
            max_length = 24 * 150

        with connection.map() as redis:
            for following_id in following_group:
                feed = feed_class(
                    following_id, max_length=max_length, redis=redis)
                feeds.append(feed)
                operation(feed, *args, **kwargs)
        return feeds


love_feedly = LoveFeedly()
