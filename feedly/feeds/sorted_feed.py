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

    def serialize_activity(self, activity):
        '''
        Serialize the activity into something we can store in Redis
        '''
        serialized_activity = self.serializer.dumps(activity)
        return serialized_activity

    def deserialize_activities(self, serialized_activities):
        '''
        Reverse the serialization
        '''
        activities = []
        for serialized, score in serialized_activities:
            activity = self.serializer.loads(serialized)
            activities.append(activity)

        return activities
