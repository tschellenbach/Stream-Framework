from stream_framework.tests.feeds.base import TestBaseFeed, implementation
from stream_framework.feeds.redis import RedisFeed
from stream_framework.activity import Activity
from stream_framework.utils import datetime_to_epoch


class CustomActivity(Activity):

    @property
    def serialization_id(self):
        '''
        Shorter serialization id than used by default
        '''
        if self.object_id >= 10 ** 10 or self.verb.id >= 10 ** 3:
            raise TypeError('Fatal: object_id / verb have too many digits !')
        if not self.time:
            raise TypeError('Cant serialize activities without a time')
        milliseconds = str(int(datetime_to_epoch(self.time) * 1000))

        # shorter than the default version
        serialization_id_str = '%s%0.2d%0.2d' % (
            milliseconds, self.object_id % 100, self.verb.id)
        serialization_id = int(serialization_id_str)

        return serialization_id


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
        assert self.activity == self.test_feed[:10][0]
        assert type(self.activity) == type(self.test_feed[0][0])
        # make sure nothing is wrong with the activity storage
