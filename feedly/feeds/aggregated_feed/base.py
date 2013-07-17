import copy
from feedly.activity import Activity
from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.base import BaseFeed
from feedly.storage.utils.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
import logging


logger = logging.getLogger(__name__)

'''
Todo, docs on how to change the serialization behaviour
compared to notification feeds
'''


class AggregatedFeed(BaseFeed):

    '''
    Aggregated feeds are an extension of the basic feed.
    The turn activities into aggregated activities by using an aggregator class.
    
    See :class:`.BaseAggregator`
    
    You can use aggregated feeds to built smart feeds, such as Facebook's newsfeed.
    Alternatively you can also use smart feeds for building complex notification systems.
    
    Have a look at fashiolista.com for the possibilities.
    
    .. note::
    
       Aggregated feeds do more work in the fanout phase. Remember that for every user
       activity the number of fanouts is equal to their number of followers.
       So with a 1000 user activities, with an average of 500 followers per user, you
       already end up running 500.000 fanout operations
       
       Since the fanout operation happens so often, you should make sure not to
       do any queries in the fanout phase or any other resource intensive operations.

    Aggregated feeds differ from feeds in a few ways:
    
    - Aggregator classes aggregate activities into aggregated activities
    - We need to update aggregated activities instead of only appending
    - Serialization is different
    '''
    #: The class to use for aggregating activities into aggregated activities
    #: also see :class:`.BaseAggregator`
    aggregator_class = RecentVerbAggregator
    #: the number of aggregated items to search to see if we match
    #: or create a new aggregated activity
    merge_max_length = 100
    
    #: we use a different timeline serializer for aggregated activities
    timeline_serializer = AggregatedActivitySerializer

    def add_many(self, activities, *args, **kwargs):
        '''
        Adds many activities to the feed
        
        :param activities: the list of activities
        '''
        if not isinstance(activities[0], Activity):
            raise ValueError('Expecting Activity not %s' % activities)
        # start by getting the aggregator
        aggregator = self.get_aggregator()

        # aggregate the activities
        new_activities = aggregator.aggregate(activities)

        # get the current aggregated activities
        current_activities = self[:self.merge_max_length]

        # merge the current activities with the new ones
        new, changed, deleted = aggregator.merge(
            current_activities, new_activities)
        # new ones we insert, changed we do a delete and insert
        to_remove = deleted
        to_add = new
        if changed:
            # sorry about the very python specific hack :)
            to_remove = zip(*changed)[0]
            to_add += zip(*changed)[1]

        # remove those which changed
        if to_remove:
            self.timeline_storage.remove_many(
                self.key, to_remove, *args, **kwargs)

        # TODO replace this, aggregator class should return this
        new_aggregated = aggregator.rank(new)

        # now add the new ones
        self.timeline_storage.add_many(self.key, to_add, *args, **kwargs)

        # now trim
        self.timeline_storage.trim(self.key, self.max_length)

        if changed:
            new_aggregated += zip(*changed)[1]

        return new_aggregated

    def contains(self, activity):
        '''
        Checks if the activity is present in any of the aggregated activities
        
        :param activity: the activity to search for
        '''
        # get all the current aggregated activities
        aggregated = self[:self.max_length]
        activities = sum([list(a.activities) for a in aggregated], [])
        # make sure we don't modify things in place
        activities = copy.deepcopy(activities)
        activity = copy.deepcopy(activity)

        activity_dict = dict()
        for a in activities:
            key = (a.verb.id, a.actor_id, a.object_id, a.target_id)
            activity_dict[key] = a

        a = activity
        activity_key = (a.verb.id, a.actor_id, a.object_id, a.target_id)
        present = activity_key in activity_dict
        return present

    def get_aggregator(self):
        '''
        Returns the class used for aggregation
        '''
        aggregator = self.aggregator_class()
        return aggregator
