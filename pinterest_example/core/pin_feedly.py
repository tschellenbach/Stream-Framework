from feedly.feed_managers.base import Feedly
from pinterest_example.core.models import Follow
from pinterest_example.core.pin_feed import AggregatedPinFeed, PinFeed, \
    UserPinFeed


class PinFeedly(Feedly):
    # this example has both a normal feed and an aggregated feed (more like
    # how facebook or wanelo uses feeds)
    feed_classes = dict(
        normal=PinFeed,
        aggregated=AggregatedPinFeed
    )
    user_feed_class = UserPinFeed

    def add_pin(self, pin):
        activity = pin.create_activity()
        # add user activity adds it to the user feed, and starts the fanout
        self.add_user_activity(pin.user_id, activity)

    def remove_pin(self, pin):
        activity = pin.create_activity()
        # removes the pin from the user's followers feeds
        self.remove_user_activity(pin.user_id, activity)

    def get_user_follower_ids(self, user_id):
        return Follow.objects.filter(target=user_id).values_list('user_id', flat=True)


feedly = PinFeedly()
