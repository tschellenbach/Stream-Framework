from feedly.activity import AggregatedActivity
import collections


class BaseAggregator(object):
    def __init__(self):
        pass
    
    def aggregate(self, activities):
        '''
        Runs the group activities (using get group)
        Ranks them using the giving ranking function
        And returns the sorted activities
        '''
        aggregate_dict = self.group_activities(activities)
        aggregated_activities = aggregate_dict.values()
        ranked_aggregates = self.rank(aggregated_activities)
        return ranked_aggregates
    
    def group_activities(self, activities):
        '''
        Groups the activities based on their group
        Found by running get_group(actvity on them)
        '''
        aggregate_dict = dict()
        for activity in activities:
            group = self.get_group(activity)
            if group not in aggregate_dict:
                aggregate_dict[group] = AggregatedActivity(group)
            aggregate_dict[group].append(activity)
        
        return aggregate_dict
    
    def get_group(self, activity):
        '''
        Returns a group to stick this activity in
        '''
        pass
    
    def rank(self, aggregated_activities):
        '''
        The ranking logic, for sorting aggregated activities
        '''
        pass
    
    
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
            aggregated_activity_ids = [a.object_id for a in aggregated_activity.activities]
            return max(aggregated_activity_ids)
            
        aggregated_activities.sort(key=sort_key)
        return aggregated_activities
        
    def get_group(self, activity):
        '''
        Returns a group to stick this activity in
        '''
        return activity.object_id % self.modulus


