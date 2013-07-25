from feedly.activity import Activity, AggregatedActivity
from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.base import BaseFeed
from feedly.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
import copy
import logging
import random


logger = logging.getLogger(__name__)


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
    # : The class to use for aggregating activities into aggregated activities
    # : also see :class:`.BaseAggregator`
    aggregator_class = RecentVerbAggregator
    # : the number of aggregated items to search to see if we match
    # : or create a new aggregated activity
    merge_max_length = 100

    # : we use a different timeline serializer for aggregated activities
    timeline_serializer = AggregatedActivitySerializer

    def add_many(self, activities, batch_interface=None):
        '''
        Adds many activities to the feed
        
        Unfortunately we can't support the batch interface.
        The writes depend on the reads.
        
        Also subsequent writes will depend on these writes.
        So no batching is possible at all.

        :param activities: the list of activities
        '''
        if activities and not isinstance(activities[0], Activity):
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
            to_remove += zip(*changed)[0]
            to_add += zip(*changed)[1]

        # remove those which changed
        if to_remove:
            self.remove_many_aggregated(to_remove)

        # TODO replace this, aggregator class should return this
        new_aggregated = aggregator.rank(new)

        # now add the new ones
        if to_add:
            self.add_many_aggregated(to_add)

        # now trim in 10 percent of the cases
        if random.randint(0, 100) <= 5:
            self.timeline_storage.trim(self.key, self.max_length)

        if changed:
            new_aggregated += zip(*changed)[1]

        return new_aggregated

    def remove_many(self, activities, batch_interface=None):
        '''
        Removes many activities from the feed
        
        :param activities: the list of activities to remove
        '''
        if activities and not isinstance(activities[0], Activity):
            raise ValueError('Expecting Activity not %s' % activities)

        # get the current aggregated activities
        # remove the activity in question
        # remove the aggregated activity if it's empty
        # possibly reaggregate the activities (not doing this)
        # its impractical since data could be lost
        current_activities = self[:]
        deleted = []
        changed = dict()
        # TODO: this method of searching for activities is super super slow
        # probably fast enough, but maybe refactor
        for aggregated in current_activities:
            # search for our activities
            for activity in activities:
                if aggregated.contains(activity):
                    original = copy.deepcopy(aggregated)
                    # see if it already changed
                    current = aggregated
                    updated = changed.get(original.group)
                    if updated:
                        current = updated[1]

                    current = copy.deepcopy(current)

                    # delete the aggregated activity if it will become empty
                    if len(current.activities) == 1:
                        deleted.append(original)
                        changed.pop(original.group, None)
                    else:
                        # otherwise just remove it and add the result to
                        # changed
                        current.remove(activity)
                        changed[original.group] = (original, current)

        # new ones we insert, changed we do a delete and insert
        to_remove = deleted
        to_add = []
        if changed:
            # sorry about the very python specific hack :)
            to_remove += zip(*changed.values())[0]
            to_add += zip(*changed.values())[1]

        # remove those which changed
        if to_remove:
            self.remove_many_aggregated(to_remove)

        # now add the new ones
        if to_add:
            self.add_many_aggregated(to_add)

    def add_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Adds the list of aggregated activities

        :param aggregated: the list of aggregated activities to add
        '''
        if aggregated and not isinstance(aggregated[0], AggregatedActivity):
            raise ValueError(
                'Expecting AggregatedActivity not %s' % aggregated)
        self.timeline_storage.add_many(self.key, aggregated, *args, **kwargs)

    def remove_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Removes the list of aggregated activities

        :param aggregated: the list of aggregated activities to remove
        '''
        if aggregated and not isinstance(aggregated[0], AggregatedActivity):
            raise ValueError(
                'Expecting AggregatedActivity not %s' % aggregated)
        self.timeline_storage.remove_many(
            self.key, aggregated, *args, **kwargs)

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
