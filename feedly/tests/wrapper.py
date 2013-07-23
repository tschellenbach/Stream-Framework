from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.redis import RedisFeed
import datetime
from feedly.verbs.base import Love as LoveVerb
from feedly.tests.utils import FakeActivity
from feedly.wrapper import FeedResultsWrapper
from feedly.feeds.cassandra import CassandraFeed


class TestWrapper(TestBaseFeed):
    feed_cls = CassandraFeed
    
    def test_feed_timestamp_order(self):
        # first we build a feed with 1000 items
        activities = []
        now = datetime.datetime.now()
        activity_dict = {}
        for i in range(1000):
            activity = FakeActivity(
                i, LoveVerb, i, i, time=now + datetime.timedelta(seconds=i))
            activities.append(activity)
            activity_dict[i] = activity
        self.feed_cls.insert_activities(activities)
        self.test_feed.add_many(activities)
        
        wrapped = FeedResultsWrapper(self.test_feed)
        
        def get_ids(results):
            return [r.object_id for r in results]
        
        self.assertEqual(get_ids(wrapped[:3]), [999, 998, 997])
        self.assertEqual(get_ids(wrapped[5:8]), [994, 993, 992]    )
        print self.test_feed[997:]
        print wrapped[997:]
        self.assertEqual(get_ids(wrapped[997:]), [2, 1, 0])
        
        print wrapped.filter(pk__lt=activity_dict[50].serialization_id)[:3]
        print wrapped.filter(pk__lt=activity_dict[950].serialization_id)[0:3]
