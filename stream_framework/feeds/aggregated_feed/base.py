from stream_framework.activity import AggregatedActivity
from stream_framework.aggregators.base import RecentVerbAggregator
from stream_framework.feeds.base import BaseFeed
from stream_framework.serializers.aggregated_activity_serializer import \
    AggregatedActivitySerializer
import copy
import logging
import random
import itertools
from stream_framework.utils.timing import timer
from collections import defaultdict
from stream_framework.utils.validate import validate_list_of_strict
from stream_framework.tests.utils import FakeActivity, FakeAggregatedActivity


logger = logging.getLogger(__name__)


class AggregatedFeed(BaseFeed):

    '''
    Aggregated feeds are an extension of the basic feed.
    They turn activities into aggregated activities by using an aggregator class.

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

    # : The class to use for storing the aggregated activity
    aggregated_activity_class = AggregatedActivity
    # : the number of aggregated items to search to see if we match
    # : or create a new aggregated activity
    merge_max_length = 20

    # : we use a different timeline serializer for aggregated activities
    timeline_serializer = AggregatedActivitySerializer

    @classmethod
    def get_timeline_storage_options(cls):
        '''
        Returns the options for the timeline storage
        '''
        options = super(AggregatedFeed, cls).get_timeline_storage_options()
        options['aggregated_activity_class'] = cls.aggregated_activity_class
        return options

    def add_many(self, activities, trim=True, current_activities=None, *args, **kwargs):
        '''
        Adds many activities to the feed

        Unfortunately we can't support the batch interface.
        The writes depend on the reads.

        Also subsequent writes will depend on these writes.
        So no batching is possible at all.

        :param activities: the list of activities
        '''
        validate_list_of_strict(
            activities, (self.activity_class, FakeActivity))
        # start by getting the aggregator
        aggregator = self.get_aggregator()

        t = timer()
        # get the current aggregated activities
        if current_activities is None:
            current_activities = self[:self.merge_max_length]
        msg_format = 'reading %s items took %s'
        logger.debug(msg_format, self.merge_max_length, t.next())

        # merge the current activities with the new ones
        new, changed, deleted = aggregator.merge(
            current_activities, activities)
        logger.debug('merge took %s', t.next())

        # new ones we insert, changed we do a delete and insert
        new_aggregated = self._update_from_diff(new, changed, deleted)
        new_aggregated = aggregator.rank(new_aggregated)

        # trim every now and then
        if trim and random.random() <= self.trim_chance:
            self.timeline_storage.trim(self.key, self.max_length)

        return new_aggregated

    def remove_many(self, activities, batch_interface=None, trim=True, *args, **kwargs):
        '''
        Removes many activities from the feed

        :param activities: the list of activities to remove
        '''
        # trim to make sure nothing we don't need is stored after the max
        # length
        self.trim()

        # allow to delete activities from a specific list of activities
        # instead of scanning max_length (eg. if the user implements a reverse index
        # based on group)
        current_activities = kwargs.pop('current_activities', None)
        if current_activities is None:
            current_activities = self.get_activity_slice(
                stop=self.max_length, rehydrate=False)

        # setup our variables
        new, deleted, changed = [], [], []
        getid = lambda a: getattr(a, 'serialization_id', a)
        activities_to_remove = set(getid(a) for a in activities)
        activity_dict = dict((getid(a), a) for a in activities)

        # first built the activity lookup dict
        activity_remove_dict = defaultdict(list)
        for aggregated in current_activities:
            for activity_id in aggregated.activity_ids:
                if activity_id in activities_to_remove:
                    activity_remove_dict[aggregated].append(activity_id)
                    activities_to_remove.discard(activity_id)
            # stop searching when we have all of the activities to remove
            if not activities_to_remove:
                break

        # stick the activities to remove in changed or remove
        hydrated_aggregated = activity_remove_dict.keys()
        if self.needs_hydration(hydrated_aggregated):
            hydrated_aggregated = self.hydrate_activities(hydrated_aggregated)
        hydrate_dict = dict((a.group, a) for a in hydrated_aggregated)

        for aggregated, activity_ids_to_remove in activity_remove_dict.items():
            aggregated = hydrate_dict.get(aggregated.group)
            if len(aggregated) == len(activity_ids_to_remove):
                deleted.append(aggregated)
            else:
                original = copy.deepcopy(aggregated)
                activities_to_remove = map(
                    activity_dict.get, activity_ids_to_remove)
                aggregated.remove_many(activities_to_remove)
                changed.append((original, aggregated))

        # new ones we insert, changed we do a delete and insert
        new_aggregated = self._update_from_diff(new, changed, deleted)
        return new_aggregated

    def add_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Adds the list of aggregated activities

        :param aggregated: the list of aggregated activities to add
        '''
        validate_list_of_strict(
            aggregated, (self.aggregated_activity_class, FakeAggregatedActivity))
        self.timeline_storage.add_many(self.key, aggregated, *args, **kwargs)

    def remove_many_aggregated(self, aggregated, *args, **kwargs):
        '''
        Removes the list of aggregated activities

        :param aggregated: the list of aggregated activities to remove
        '''
        validate_list_of_strict(
            aggregated, (self.aggregated_activity_class, FakeAggregatedActivity))
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
        aggregator = self.aggregator_class(
            self.aggregated_activity_class, self.activity_class)
        return aggregator

    def _update_from_diff(self, new, changed, deleted):
        '''
        Sends the add and remove commands to the storage layer based on a diff
        of

        :param new: list of new items
        :param changed: list of tuples (from, to)
        :param deleted: list of things to delete
        '''
        msg_format = 'now updating from diff new: %s changed: %s deleted: %s'
        logger.debug(msg_format, *map(len, [new, changed, deleted]))
        to_remove, to_add = self._translate_diff(new, changed, deleted)

        # remove those which changed
        with self.get_timeline_batch_interface() as batch_interface:
            if to_remove:
                self.remove_many_aggregated(
                    to_remove, batch_interface=batch_interface)

        # now add the new ones
        with self.get_timeline_batch_interface() as batch_interface:
            if to_add:
                self.add_many_aggregated(
                    to_add, batch_interface=batch_interface)

        logger.debug(
            'removed %s, added %s items from feed %s', len(to_remove), len(to_add), self)

        # return the merge of these two
        new_aggregated = new[:]
        if changed:
            new_aggregated += list(zip(*changed))[1]

        self.on_update_feed(to_add, to_remove)
        return new_aggregated

    def _translate_diff(self, new, changed, deleted):
        '''
        Translates a list of new changed and deleted into
        Add and remove instructions

        :param new: list of new items
        :param changed: list of tuples (from, to)
        :param deleted: list of things to delete
        :returns: a tuple with a list of items to remove and to add

        **Example**::

            new = [AggregatedActivity]
            deleted = [AggregatedActivity]
            changed = [(AggregatedActivity, AggregatedActivity)]
            to_remove, to_delete = feed._translate_diff(new, changed, deleted)
        '''
        # validate this data makes sense
        error_format = 'please only send aggregated activities not %s'
        flat_changed = sum(map(list, changed), [])
        for aggregated_activity in itertools.chain(new, flat_changed, deleted):
            if not isinstance(aggregated_activity, AggregatedActivity):
                raise ValueError(error_format % aggregated_activity)

        # now translate the instructions
        to_remove = deleted[:]
        to_add = new[:]
        if changed:
            to_remove += [c[0] for c in changed]
            to_add += [c[1] for c in changed]
        return to_remove, to_add
