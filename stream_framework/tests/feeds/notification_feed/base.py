from stream_framework.activity import NotificationActivity
from stream_framework.verbs.base import Love as LoveVerb, Comment as CommentVerb, Follow as FollowVerb
from stream_framework.feeds.notification_feed.base import BaseNotificationFeed
from stream_framework.tests.feeds.aggregated_feed.base import TestAggregatedFeed
from datetime import datetime, timedelta
import unittest


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.feed_cls == BaseNotificationFeed:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class TestBaseNotificationFeed(TestAggregatedFeed):

    feed_cls = BaseNotificationFeed
    aggregated_activity_class = NotificationActivity

    def create_activities(self, verb, object_id, count):
        return [self.activity_class(actor = x,
                                    verb = verb,
                                    object = object_id,
                                    target = x,
                                    time=datetime.now() + timedelta(seconds=x,
                                                                    minutes=object_id),
                                    extra_context = dict(x=x))
                for x in range(0, count)]

    def setUp(self):
        super(TestBaseNotificationFeed, self).setUp()

        self.loves = self.create_activities(LoveVerb, 1, 5)
        self.comments = self.create_activities(CommentVerb, 2, 5)
        self.followers = self.create_activities(FollowVerb, self.user_id, 5)

        aggregator = self.test_feed.get_aggregator()
        self.aggregated_love = aggregator.aggregate(self.loves)[0]
        self.aggregated_comment = aggregator.aggregate(self.comments)[0]
        self.aggregated_follower = aggregator.aggregate(self.followers)[0]

        self.follower_id = self.aggregated_follower.serialization_id
        self.comment_id = self.aggregated_comment.serialization_id
        self.love_id  = self.aggregated_love.serialization_id

    def assert_activity_markers(self, aggregated_activity, seen=False, read=False):
        self.assertEqual(aggregated_activity.is_seen, seen)
        self.assertEqual(aggregated_activity.is_read, read)

    def assert_activities_markers(self, aggregated_activities, seen=False, read=False):
        for aggregated_activity in aggregated_activities:
            self.assert_activity_markers(aggregated_activity, seen, read)

    @implementation
    def test_add_activities(self):
        self.test_feed.add_many(self.loves[:-1])
        self.test_feed.mark_all(seen=True, read=True)

        self.test_feed.add(self.loves[-1])
        self.assert_activities_markers(self.test_feed[:])
        self.assertEqual(self.test_feed[:], [self.aggregated_love])

        self.test_feed.add_many(self.comments)
        self.assertEqual(self.test_feed[:], [self.aggregated_comment, self.aggregated_love])
        self.assert_activities_markers(self.test_feed[:])

    @implementation
    def test_add_many_aggregated_activities(self):
        self.test_feed.add_many_aggregated([self.aggregated_follower])
        self.assertEqual(self.test_feed[:], [self.aggregated_follower])
        self.assert_activities_markers(self.test_feed[:])

        self.test_feed.add_many_aggregated([self.aggregated_comment, self.aggregated_love])
        self.assertEqual(self.test_feed[:], [self.aggregated_follower, self.aggregated_comment, self.aggregated_love])
        self.assert_activities_markers(self.test_feed[:])

    @implementation
    def test_remove_activities(self):
        self.test_feed.add_many(self.loves)
        self.test_feed.remove_many(self.loves)

        self.assertEqual(self.test_feed[:], [])
        self.assertEqual(self.test_feed.count_unseen(), 0)
        self.assertEqual(self.test_feed.count_unread(), 0)

    @implementation
    def test_remove_many_aggregated_activities(self):
        self.test_feed.add_many(self.followers + self.comments + self.loves)

        self.test_feed.remove_many_aggregated([self.aggregated_follower])
        self.assertEqual(self.test_feed[:], [self.aggregated_comment, self.aggregated_love])
        self.assert_activities_markers(self.test_feed[:])

        self.test_feed.remove_many_aggregated([self.aggregated_comment, self.aggregated_love])
        self.assertEqual(self.test_feed[:], [])
        self.assertEqual(self.test_feed.count_unseen(), 0)
        self.assertEqual(self.test_feed.count_unread(), 0)

    @implementation
    def test_mark_aggregated_activity(self):
        self.test_feed.add_many(self.followers + self.comments + self.loves)
        self.assert_activities_markers(self.test_feed[0:1], seen=False, read=False)

        self.test_feed.mark_activity(self.follower_id)
        self.assert_activities_markers(self.test_feed[0:1], seen=True, read=False)
        self.assert_activities_markers(self.test_feed[1:])

        self.test_feed.mark_activity(self.follower_id, read=True)
        self.assert_activities_markers(self.test_feed[0:1], seen=True, read=True)
        self.assert_activities_markers(self.test_feed[1:])

        self.test_feed.mark_activity(self.comment_id, read=True)
        self.assert_activities_markers(self.test_feed[0:2], seen=True, read=True)
        self.assert_activities_markers(self.test_feed[2:])

    @implementation
    def test_mark_aggregated_activities(self):
        self.test_feed.add_many(self.followers + self.comments + self.loves)
        self.assert_activities_markers(self.test_feed[:], seen=False, read=False)

        self.test_feed.mark_activities([self.follower_id, self.comment_id], read=False)
        self.assert_activities_markers(self.test_feed[0:2], seen=True, read=False)
        self.assert_activities_markers(self.test_feed[2:])

        self.test_feed.mark_activities([self.follower_id, self.comment_id], read=True)
        self.assert_activities_markers(self.test_feed[0:2], seen=True, read=True)
        self.assert_activities_markers(self.test_feed[2:])

        self.test_feed.mark_activities([self.follower_id, self.comment_id, self.love_id], read=True)
        self.assert_activities_markers(self.test_feed[:], seen=True, read=True)

    @implementation
    def test_mark_all_aggregated_activities_as_seen(self):
        self.test_feed.add_many(self.followers + self.comments + self.loves)
        self.assert_activities_markers(self.test_feed[:], seen=False, read=False)
        self.test_feed.mark_all()
        self.assert_activities_markers(self.test_feed[:], seen=True, read=False)

    @implementation
    def test_mark_all_aggreagted_activities_as_read(self):
        self.test_feed.add_many(self.followers + self.comments + self.loves)
        self.assert_activities_markers(self.test_feed[:], seen=False, read=False)
        self.test_feed.mark_all(read=True)
        self.assert_activities_markers(self.test_feed[:], seen=True, read=True)

    @implementation
    def test_delete_feed(self):
        self.test_feed.add_many(self.loves)
        self.assertEqual(self.test_feed.count_unseen(), 1)
        self.assertEqual(self.test_feed.count_unread(), 1)

        self.test_feed.delete()
        self.assertEqual(self.test_feed.count_unseen(), 0)
        self.assertEqual(self.test_feed.count_unread(), 0)
