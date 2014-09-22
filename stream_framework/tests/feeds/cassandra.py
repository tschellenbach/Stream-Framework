from stream_framework.tests.feeds.base import TestBaseFeed, implementation
import pytest
from stream_framework.feeds.cassandra import CassandraFeed
from stream_framework.utils import datetime_to_epoch
from stream_framework.activity import Activity


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


class CassandraCustomFeed(CassandraFeed):
    activity_class = CustomActivity


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraBaseFeed(TestBaseFeed):
    feed_cls = CassandraFeed

    def test_add_insert_activity(self):
        pass

    def test_add_remove_activity(self):
        pass


@pytest.mark.usefixtures("cassandra_reset")
class TestCassandraCustomFeed(TestBaseFeed):
    feed_cls = CassandraCustomFeed
    activity_class = CustomActivity

    def test_add_insert_activity(self):
        pass

    def test_add_remove_activity(self):
        pass

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
