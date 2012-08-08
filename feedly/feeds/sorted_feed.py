from feedly.feeds.base import BaseFeed
from feedly.serializers.pickle_serializer import PickleSerializer
import logging
logger = logging.getLogger(__name__)


class SortedFeed(BaseFeed):
    max_length = 5
    key_format = 'feedly:sorted_feed:%s'


