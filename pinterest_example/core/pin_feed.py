from django.conf import settings
from utils.loading import import_by_path


BaseFeed = import_by_path(settings.FEEDLY_FEED_CLASS)

class PinFeed(BaseFeed):
    pass
