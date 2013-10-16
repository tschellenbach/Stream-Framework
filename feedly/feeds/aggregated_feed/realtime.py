import copy
from feedly.activity import EphemeralAggregatedActivity
from feedly.feeds.aggregated_feed.base import AggregatedFeed


class RealTimeAggregatedFeed(AggregatedFeed):
    '''
    An aggregated feed implementation that does not store the feed
    The activities stored in the source_feed_class are aggregated 
    in realtime.

    '''
    source_feed_class = None
    prefetch_ratio = 10
    max_read_attempts = 3
    default_read_limit = 100

    def __init__(self, user_id):
        self.feed = self.source_feed_class(user_id)

    def get_aggregator(self):
        # makes sure that the aggregator is using EphemeralAggregatedActivity
        # this allow us to switch from written AggregataedFeed to RealTimeAggregatedFeed painless
        aggregator_class = self.aggregator_class
        if not issubclass(self.aggregator_class.aggregation_class, EphemeralAggregatedActivity):
            aggregator_class.aggregation_class = EphemeralAggregatedActivity
        return aggregator_class()

    def fix_aggregation_slice(self, aggregations, activities):
        '''
        makes sure the sorted list of activities are not skipping any items 
        from the list of activities present in the feed

        eg. (using ints instead of real activities)
        feed = [1,2,3,4,5,6,7,8,9,10,11,12,13]
        aggregations = [[1,3,5], [6,7,8], [9,11,13]]

        '''
        selected_activities = sum([a.activities for a in aggregations], [])
        activities = sorted(activities, reversed=True)
        selected_activities = sorted(selected_activities, reversed=True)
        skipped_activities = [a for a in activities if a < selected_activities[-1] or a in selected_activities]
        aggregator = self.get_aggregator()
        new, changed, deleted = aggregator.merge(aggregations, skipped_activities)
        to_remove, to_add = self._translate_diff(new, changed, deleted)
        for a in to_remove:
            aggregations.remove(a)
        return sorted((aggregations + to_add), reversed=True)

    def get_activity_slice(self, start=None, stop=None, rehydrate=True):
        attempts = 0
        results = []
        request_size = (stop or self.default_read_limit) - (start or 0)
        prefetch_size = request_size * self.prefetch_ratio
        p_start = (start or 0)
        p_stop = (stop or self.default_read_limit)
        while attempts < self.max_read_attempts and len(results) < request_size:
            p_stop += prefetch_size
            activities = self.feed[p_start:p_stop]
            results += self.get_aggregator().merge(results, activities)[0]
            # looks like we reached the end of the feed
            if len(activities) < (p_stop - p_start):
                break
            p_start = p_stop
            attempts += 1
        if len(results) > request_size:
            # looks like we got more than what we looked for
            results = self.fix_aggregation_slice(results[:request_size])
        return results[:request_size]

    def _clone(self):
        feed_copy = copy.copy(self)
        feed_copy.feed = self.feed._clone()
        return feed_copy

    def filter(self, **kwargs):
        new = self._clone()
        new.feed._filter_kwargs.update(kwargs)
        return new
