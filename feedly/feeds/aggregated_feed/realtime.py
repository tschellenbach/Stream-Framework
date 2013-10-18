import copy
from feedly.activity import EphemeralAggregatedActivity
from feedly.feeds.aggregated_feed.base import AggregatedFeed
from functools import wraps


def noop_decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        pass
    return wrapper


class RealTimeAggregatedFeed(AggregatedFeed):
    '''
    An aggregated feed implementation that does not store the feed
    The activities stored in the source_feed_class are aggregated 
    in realtime.

    '''
    source_feed_class = None
    prefetch_ratio = 20
    max_read_attempts = 3
    default_read_limit = 100
        
    insert_activities = noop_decorator(AggregatedFeed.insert_activities)
    remove_activity = noop_decorator(AggregatedFeed.remove_activity)
    add_many = noop_decorator(AggregatedFeed.add_many)
    remove_many = noop_decorator(AggregatedFeed.remove_many)
    trim = noop_decorator(AggregatedFeed.trim)
    count = noop_decorator(AggregatedFeed.count)
    delete = noop_decorator(AggregatedFeed.delete)
    index_of = noop_decorator(AggregatedFeed.index_of)

    def __init__(self, user_id):
        self.feed = self.source_feed_class(user_id)

    def get_aggregator(self):
        # makes sure that the aggregator is using EphemeralAggregatedActivity
        # this allow us to switch from written AggregataedFeed to RealTimeAggregatedFeed painless
        aggregator_class = self.aggregator_class
        if not issubclass(self.aggregator_class.aggregation_class, EphemeralAggregatedActivity):
            aggregator_class.aggregation_class = EphemeralAggregatedActivity
        return aggregator_class()

    def fix_aggregation_slice(self, selected_aggregations, excluded_activities):
        '''
        make sure that aggregated activities in selected_aggregations and excluded_activities
        dont overlap (eg. one activity in excluded_activities is more recent than one in selected_activities)

        '''
        selected_activities = sum([a.activities for a in selected_aggregations], [])
        not_selected_activities = sum([a.activities for a in excluded_activities], [])

        assert len(set(selected_activities).intersection(set(not_selected_activities))) == 0

        if len(not_selected_activities) == 0:
            return selected_aggregations

        most_recent_not_selected_activity = max(not_selected_activities)

        if min(selected_activities) > most_recent_not_selected_activity:
            return selected_aggregations

        for aggregated in selected_aggregations:
            for activity in aggregated.activities:
                if activity < most_recent_not_selected_activity:
                    aggregated.remove(activity)
        return selected_aggregations

    def get_activity_slice(self, start=None, stop=None, rehydrate=True):
        if start not in (0, None):
            raise TypeError('Offsets are not supported')
        attempts = p_start = 0
        results = []
        request_size = (stop or self.default_read_limit)
        prefetch_size = request_size * self.prefetch_ratio
        p_stop = (stop or self.default_read_limit)
        while attempts < self.max_read_attempts and len(results) < request_size:
            p_stop += prefetch_size
            print p_start, p_stop
            activities = self.feed[p_start:p_stop]
            results += self.get_aggregator().merge(results, activities)[0]
            if len(activities) < (p_stop - p_start):
                break
            p_start = p_stop
            attempts += 1
        results = sorted(results, reverse=True)
        return self.fix_aggregation_slice(results[:request_size], results[request_size:])

    def _clone(self):
        feed_copy = copy.copy(self)
        feed_copy.feed = self.feed._clone()
        return feed_copy

    def filter(self, **kwargs):
        new = self._clone()
        new.feed._filter_kwargs.update(kwargs)
        return new
