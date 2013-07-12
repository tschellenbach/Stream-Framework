from feedly.activity import AggregatedActivity
from copy import deepcopy


class BaseAggregator(object):
    '''
    Aggregators implement the combining of multiple activities into aggregated activities.
    
    The two most important methods are
    aggregate and merge
    
    Aggregate takes a list of activities and turns it into a list of aggregated activities
    
    Merge takes two lists of aggregated activities and returns a list of new and changed aggregated activities
    '''
    aggregation_class = AggregatedActivity

    def __init__(self):
        pass

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
        aggregated_activities = aggregate_dict.values()
        ranked_aggregates = self.rank(aggregated_activities)
        return ranked_aggregates

    def merge(self, aggregated, new_aggregated):
        '''
        :param aggregated: A list of aggregated activities
        :param new_aggregated: A list of the new aggregated activities
        :returns tuple: Returns new, changed
        
        Merges two lists of aggregated activities and returns the new aggregated
        activities and a from, to mapping of the changed aggregated activities
        
        **Example** ::
        
            aggregator = ModulusAggregator()
            activities = [Activity(1), Activity(2)]
            aggregated_activities = aggregator.aggregate(activities)
            activities = [Activity(3), Activity(4)]
            aggregated_activities2 = aggregator.aggregate(activities)
            new, changed = aggregator.merge(aggregated_activities, aggregated_activities2)
            for activity in new:
                print activity
                
            for from, to in changed:
                print 'changed from %s to %s' % (from, to)
        
        '''
        current_activities_dict = dict([(a.group, a) for a in aggregated])
        new = []
        changed = []
        for aggregated in new_aggregated:
            if aggregated.group not in current_activities_dict:
                new.append(aggregated)
            else:
                current_aggregated = current_activities_dict.get(
                    aggregated.group)
                new_aggregated = deepcopy(current_aggregated)
                for activity in aggregated.activities:
                    new_aggregated.append(activity)
                changed.append((current_aggregated, new_aggregated))
        return new, changed, []

    def group_activities(self, activities):
        '''
        Groups the activities based on their group
        Found by running get_group(actvity on them)
        '''
        aggregate_dict = dict()
        for activity in activities:
            group = self.get_group(activity)
            if group not in aggregate_dict:
                aggregate_dict[group] = self.aggregation_class(group)
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


class ModulusAggregator(BaseAggregator):

    '''
    Example aggregator using modulus
    '''

    def __init__(self, modulus=3):
        '''
        Set the modulus we want to use
        '''
        self.modulus = modulus

    def rank(self, aggregated_activities):
        '''
        The ranking logic, for sorting aggregated activities
        '''
        def sort_key(aggregated_activity):
            aggregated_activity_ids = [
                a.object_id for a in aggregated_activity.activities]
            return max(aggregated_activity_ids)

        aggregated_activities.sort(key=sort_key)
        return aggregated_activities

    def get_group(self, activity):
        '''
        Returns a group to stick this activity in
        '''
        return activity.object_id % self.modulus


class RecentVerbAggregator(BaseAggregator):

    '''
    Aggregates based on the same verb and same time period
    '''

    def rank(self, aggregated_activities):
        '''
        The ranking logic, for sorting aggregated activities
        '''
        def sort_key(aggregated_activity):
            aggregated_activity_ids = [
                a.object_id for a in aggregated_activity.activities]
            return max(aggregated_activity_ids)

        aggregated_activities.sort(key=sort_key)
        return aggregated_activities

    def get_group(self, activity):
        '''
        Returns a group based on the day and verb
        '''
        verb = activity.verb.id
        date = activity.time.date()
        group = '%s-%s' % (verb, date)
        return group


class FashiolistaAggregator(BaseAggregator):
    '''
    Aggregated by 
    - user
    - type
    - datetime
    
    Or when we have more than 2 people loving the same item, aggregate by
    - item
    '''
    def aggregate(self, activities):
        '''
        Runs the group activities (using get group)
        Ranks them using the giving ranking function
        And returns the sorted activities
        '''
        user_aggregate_dict = self.group_activities(activities, group_type='user')
        entity_aggregate_dict = self.group_activities(activities, group_type='entity')

        aggregate_dict = self.merge_group_types(user_aggregate_dict, entity_aggregate_dict)

        aggregated_activities = aggregate_dict.values()
        ranked_aggregates = self.rank(aggregated_activities)

        return ranked_aggregates

    def merge_group_types(self, user_aggregate_dict, entity_aggregate_dict):
        redundant_activities = []

        for k, v in entity_aggregate_dict.copy().items():
            if len(v.activities) < 2:
                del entity_aggregate_dict[k]
            else:
                redundant_activities.extend(v.activities)


        for k, v in user_aggregate_dict.copy().items():
            v.activities = [a for a in v.activities if a not in redundant_activities]
            if not v.activities:
                del user_aggregate_dict[k]

        aggregate_dict = entity_aggregate_dict
        aggregate_dict.update(user_aggregate_dict)
        return aggregate_dict

    def group_activities(self, activities, **kwargs):
        '''
        Groups the activities based on their group
        Found by running get_group(actvity on them)
        '''
        aggregate_dict = dict()
        for activity in activities:
            group = self.get_group(activity, **kwargs)
            if group not in aggregate_dict:
                aggregate_dict[group] = self.aggregation_class(group)
            aggregate_dict[group].append(activity)

        return aggregate_dict

    def get_group(self, activity, group_type='entity'):
        '''
        Returns a group based on the day and verb
        '''
        if group_type == 'entity':
            group_type_key = activity.object_id  
        elif group_type == group_type == 'user':
            group_type_key = activity.actor_id
        else:
            raise "Invalid group type!"

        verb = activity.verb.id
        time = activity.time
        group = '%s-%s-%s-%s' % (group_type, group_type_key, verb, time.timetuple()[:4])
        return group

    def rank(self, aggregated_activities):
        aggregated_activities.sort(key=lambda x: x.activities[0].time)
        return aggregated_activities

    def merge(self, aggregated, new_aggregated):
        '''
        Returns
        new, changed, deleted
        where changed is activity list with tuples of old, new
        '''
        # construct old aggregated dict and build list of total activites for 
        # new aggregation round
        original_activities_dict = {}
        activities = []
        for aa in aggregated:
            original_activities_dict[aa.group] = aa
            activities.extend(aa.activities)
        for naa in new_aggregated:
            activities.extend(naa.activities)

        new_aggregated = self.aggregate(activities)
        
        new, changed, deleted = [], [], original_activities_dict.keys()

        # diff new/changed/deleted keys
        for naa in new_aggregated:
            deleted = [k for k in deleted if k != naa.group]

            if naa.group not in original_activities_dict:
                new.append(naa)
            elif naa != original_activities_dict[naa.group]:
                changed.append((original_activities_dict[naa.group], naa))

        deleted = [original_activities_dict[k] for k in deleted]
        print 'new', new
        print 'changed', changed
        print 'deleted', deleted

        return new, changed, deleted

