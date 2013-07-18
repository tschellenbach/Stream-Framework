from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed
from feedly.feeds.aggregated_feed.notification_feed import RedisNotificationFeed


class TestNotificationFeed(TestAggregatedFeed):
    feed_cls = RedisNotificationFeed

    def test_aggregated_feed(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        # test by sticking the items in the feed
        for activity in self.activities:
            self.test_feed.add(activity)
        results = self.test_feed[:3]
        # compare it to a direct call on the aggregator
        aggregator = self.test_feed.get_aggregator()
        aggregated_activities = aggregator.aggregate(self.activities)
        # check the feed
        assert results[0].actor_ids == aggregated_activities[0].actor_ids

    def test_remove(self):
        '''
        Test the aggregated feed by comparing the aggregator class
        to the output of the feed
        '''
        aggregator = self.test_feed.get_aggregator()
        # test by sticking the items in the feed
        activity = self.activities[0]
        aggregated_activities = aggregator.aggregate([activity])
        aggregated_activity = aggregated_activities[0]
        self.test_feed.add(activity)
        assert len(self.test_feed[:10]) == 1
        # compare it to a direct call on the aggregator
        self.test_feed.remove(aggregated_activity)
        assert len(self.test_feed[:10]) == 0
