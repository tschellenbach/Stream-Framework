from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.base import BaseFeed
from feedly.storage.utils.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
import copy
import logging

logger = logging.getLogger(__name__)


class AggregatedFeed(BaseFeed):

    '''
    Aggregated feeds are somewhat different

    - Aggregator classes aggregate activities into aggregated activities
    - We need to update aggregated activities instead of only appending
    - Serialization is different

    This can be used for smart feeds (like Facebook) or possibly
    notification systems
    '''
    timeline_serializer = AggregatedActivitySerializer
    aggregator_class = RecentVerbAggregator

    def add_many(self, activities, *args, **kwargs):
        # start by getting the aggregator
        aggregator = self.get_aggregator()

        # aggregate the activities
        new_activities = aggregator.aggregate(activities)

        # get the current aggregated activities
        current_activities = self[:self.max_length]

        # merge the current activities with the new ones
        new, changed = aggregator.merge(current_activities, new_activities)
        # new ones we insert, changed we do a delete and insert
        to_remove = []
        to_add = new
        if changed:
            # sorry about the very python specific hack :)
            to_remove = zip(*changed)[0]
            to_add += zip(*changed)[1]

        # remove those which changed
        if to_remove:
            self.timeline_storage.remove_many(
                self.key, to_remove, *args, **kwargs)
        # now add the new ones
        self.timeline_storage.add_many(self.key, to_add, *args, **kwargs)
        # now trim
        self.timeline_storage.trim(self.key, self.max_length)

    def get_results(self, start=None, stop=None):
        '''
        Only query the timeline storage, not the activity storage in this case
        '''
        activities = self.timeline_storage.get_many(self.key, start, stop)
        return sorted(activities, reverse=True)

    def contains(self, activity):
        # get all the current aggregated activities
        aggregated = self[:self.max_length]
        activities = sum([list(a.activities) for a in aggregated], [])
        # make sure we don't modify things in place
        activities = copy.deepcopy(activities)
        activity = copy.deepcopy(activity)

        # we don't care about the time of the activity, just the contents
        activity.time = None
        for activity in activities:
            activity.time = None

        present = activity in activities
        return present

    def get_aggregator(self):
        '''
        Returns the class used for aggregation
        '''
        aggregator = self.aggregator_class()
        return aggregator