from feedly.feed_managers.base import Feedly
from feedly.marker import FeedEndMarker
from feedly.utils import chunks
from pinterest_example.core.pin_feed import PinFeed
import logging
from pinterest_example.core.models import Follow


logger = logging.getLogger(__name__)


# functions used in tasks need to be at the main level of the module
def add_operation(feed, activity_id):
    feed.add(activity_id)


def remove_operation(feed, activity_id):
    feed.remove(activity_id)


class PinFeedly(Feedly):
    # The size of the chunks for doing a fanout
    FANOUT_CHUNK_SIZE = 10000

    def add_pin(self, pin):
        '''
        Store the new love and then fanout to all your followers

        This is really write intensive
        Reads are super light though
        '''
        activity = pin.create_activity()
        self.feed_class.insert_activity(activity)
        feeds = self._fanout(
            pin.user,
            add_operation,
            activity_id=activity.serialization_id
        )
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
        feed = self.get_user_feed(follow.user_id)
        target_loves = follow.target.get_profile(
        ).loves()[:self.MAX_FOLLOW_LOVES]
        activities = []
        for love in target_loves:
            activity = self.create_love_activity(love)
            activities.append(activity)
        feed.add_many(activities)
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
            feed = self.get_user_feed(follow.user_id)
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

    def get_follower_ids(self, user):
        '''
        Wrapper for retrieving all the followers for a user
        '''
        follower_ids = Follow.objects.filter(target=user).values_list('user_id', flat=True)
        return follower_ids

    def get_follower_groups(self, user):
        '''
        Gets the active and inactive follower groups together with their
        feed max length
        '''
        follower_ids = self.get_follower_ids(user=user)
        follower_groups = chunks(follower_ids, self.FANOUT_CHUNK_SIZE)
        return follower_groups


feedly = PinFeedly(PinFeed)
