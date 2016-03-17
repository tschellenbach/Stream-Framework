from stream_framework.activity import AggregatedActivity, Activity
from copy import deepcopy
from stream_framework.exceptions import DuplicateActivityException


class BaseAggregator(object):

    '''
    Aggregators implement the combining of multiple activities into aggregated activities.

    The two most important methods are
    aggregate and merge

    Aggregate takes a list of activities and turns it into a list of aggregated activities

    Merge takes two lists of aggregated activities and returns a list of new and changed aggregated activities
    '''

    aggregated_activity_class = AggregatedActivity
    activity_class = Activity

    def __init__(self, aggregated_activity_class=None, activity_class=None):
        '''
        :param aggregated_activity_class: the class which we should use
        for returning the aggregated activities
        '''
        if aggregated_activity_class is not None:
            self.aggregated_activity_class = aggregated_activity_class
        if activity_class is not None:
            self.activity_class = activity_class

    def aggregate(self, activities):
        '''

        :param activties: A list of activities
        :returns list: A list of aggregated activities

        Runs the group activities (using get group)
        Ranks them using the giving ranking function
        And returns the sorted activities

        **Example** ::

            aggregator = ModulusAggregator()
            activities = [Activity(1), Activity(2)]
            aggregated_activities = aggregator.aggregate(activities)

        '''
        aggregate_dict = self.group_activities(activities)
        aggregated_activities = list(aggregate_dict.values())
        ranked_aggregates = self.rank(aggregated_activities)
        return ranked_aggregates

    def merge(self, aggregated, activities):
        '''
        :param aggregated: A list of aggregated activities
        :param activities: A list of the new activities
        :returns tuple: Returns new, changed

        Merges two lists of aggregated activities and returns the new aggregated
        activities and a from, to mapping of the changed aggregated activities

        **Example** ::

            aggregator = ModulusAggregator()
            activities = [Activity(1), Activity(2)]
            aggregated_activities = aggregator.aggregate(activities)
            activities = [Activity(3), Activity(4)]
            new, changed = aggregator.merge(aggregated_activities, activities)
            for activity in new:
                print activity

            for from, to in changed:
                print 'changed from %s to %s' % (from, to)

        '''
        current_activities_dict = dict([(a.group, a) for a in aggregated])
        new = []
        changed = []
        new_aggregated = self.aggregate(activities)
        for aggregated in new_aggregated:
            if aggregated.group not in current_activities_dict:
                new.append(aggregated)
            else:
                current_aggregated = current_activities_dict.get(
                    aggregated.group)
                new_aggregated = deepcopy(current_aggregated)
                for activity in aggregated.activities:
                    try:
                        new_aggregated.append(activity)
                    except DuplicateActivityException:
                        pass
                if current_aggregated.activities != new_aggregated.activities:
                    changed.append((current_aggregated, new_aggregated))
        return new, changed, []

    def group_activities(self, activities):
        '''
        Groups the activities based on their group
        Found by running get_group(actvity on them)
        '''
        aggregate_dict = dict()
        # make sure that if we aggregated multiple activities
        # they end up in serialization_id desc in the aggregated activity
        activities = list(activities)
        activities.sort()
        for activity in activities:
            group = self.get_group(activity)
            if group not in aggregate_dict:
                aggregate_dict[group] = self.aggregated_activity_class(group)
            aggregate_dict[group].append(activity)

        return aggregate_dict

    def get_group(self, activity):
        '''
        Returns a group to stick this activity in
        '''
        raise ValueError('not implemented')

    def rank(self, aggregated_activities):
        '''
        The ranking logic, for sorting aggregated activities
        '''
        raise ValueError('not implemented')


class RecentRankMixin(object):

    '''
    Most recently updated aggregated activities are ranked first.
    '''

    def rank(self, aggregated_activities):
        '''
        The ranking logic, for sorting aggregated activities
        '''
        aggregated_activities.sort(key=lambda a: a.updated_at, reverse=True)
        return aggregated_activities


class RecentVerbAggregator(RecentRankMixin, BaseAggregator):

    '''
    Aggregates based on the same verb and same time period
    '''

    def get_group(self, activity):
        '''
        Returns a group based on the day and verb
        '''
        verb = activity.verb.id
        date = activity.time.date()
        group = '%s-%s' % (verb, date)
        return group


class NotificationAggregator(RecentRankMixin, BaseAggregator):

    '''
    Aggregates based on the same verb, object and day
    '''

    def get_group(self, activity):
        '''
        Returns a group based on the verb, object and day
        '''
        verb = activity.verb.id
        object_id = activity.object_id
        date = activity.time.date()
        group = '%s-%s-%s' % (verb, object_id, date)
        return group
