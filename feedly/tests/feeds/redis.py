from feedly.tests.feeds.base import TestBaseFeed, implementation
from feedly.feeds.redis import RedisFeed
from feedly.activity import Activity


class CustomActivity(Activity):
    pass


class RedisCustom(RedisFeed):
    activity_class = CustomActivity


class TestRedisFeed(TestBaseFeed):
    feed_cls = RedisFeed


class TestCustomRedisFeed(TestBaseFeed):
    '''
    Test if the option to customize the activity class works without troubles
    '''
    feed_cls = RedisCustom
    activity_class = CustomActivity
    
    @implementation
    def test_custom_activity(self):
        assert self.test_feed.count() == 0
        self.feed_cls.insert_activity(
            self.activity
        )
        self.test_feed.add(self.activity)
        assert self.test_feed.count() == 1
        assert [self.activity] == self.test_feed[0]
        assert type(self.activity) == type(self.test_feed[0][0])
    
