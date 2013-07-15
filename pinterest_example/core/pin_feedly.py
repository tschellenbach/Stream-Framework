from django.conf import settings
from feedly.feed_managers.base import Feedly
from pinterest_example.core.models import Follow
from pinterest_example.core.utils.loading import import_by_path


class PinFeedly(Feedly):

    def add_pin(self, pin):
        activity = pin.create_activity()
        self.add_user_activity(self.feed_class, pin.user_id, activity)
        self.add_user_activity(self.aggregated_feed_class, pin.user_id, activity)

    def get_user_follower_ids(self, user_id):
        return Follow.objects.filter(target=user_id).values_list('user_id', flat=True)


feedly = PinFeedly(
    import_by_path(settings.FEEDLY_FEED_CLASS),
    import_by_path(settings.FEEDLY_USER_FEED_CLASS),
    timeline_storage_options=settings.FEEDLY_TIMELINE_STORAGE_OPTIONS,
    activity_storage_options=settings.FEEDLY_ACTIVITY_STORAGE_OPTIONS,
    fanout_chunk_size=10000,
    follow_activity_limit=5000
)
