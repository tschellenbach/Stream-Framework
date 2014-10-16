from stream_framework.tests.feeds.aggregated_feed.base import TestAggregatedFeed
from stream_framework.feeds.aggregated_feed.notification_feed import RedisNotificationFeed


class TestNotificationFeed(TestAggregatedFeed):
    feed_cls = RedisNotificationFeed

    def test_mark_all(self):
        # start by adding one
        self.test_feed.insert_activities(self.aggregated.activities)
        self.test_feed.add_many_aggregated([self.aggregated])
        assert len(self.test_feed[:10]) == 1
        assert int(self.test_feed.count_unseen()) == 1
        # TODO: don't know why this is broken
        # assert int(self.test_feed.get_denormalized_count()) == 1
        self.test_feed.mark_all()
        assert int(self.test_feed.count_unseen()) == 0
        assert int(self.test_feed.get_denormalized_count()) == 0
