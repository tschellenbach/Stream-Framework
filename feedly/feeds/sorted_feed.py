from feedly.feeds.base import BaseFeed
from feedly.serializers.pickle_serializer import PickleSerializer
import logging
logger = logging.getLogger(__name__)


class SortedFeed(BaseFeed):
    max_length = 5
    key_format = 'feedly:sorted_feed:%s'
    
    def add(self, activity):
        '''
        Make sure results are actually cleared to max items
        '''
        activities = [activity]
        result = self.add_many(activities)[0]
        return result
    
    def remove(self, activity):
        '''
        Delegated to remove many
        '''
        activities = [activity]
        result = self.remove_many(activities)[0]
        return result
