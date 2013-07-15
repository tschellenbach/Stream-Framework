import datetime
from feedly.feeds.base import BaseFeed
from feedly.feed_managers.base import Feedly
from feedly.tests.utils import Pin
from feedly.tests.utils import FakeActivity
from feedly.verbs.base import Love as LoveVerb
from mock import patch
import unittest


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.__class__ == BaseFeedlyTest:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class BaseFeedlyTest(unittest.TestCase):
    manager_class = Feedly

    def setUp(self):
        self.feedly = self.manager_class()
        self.pin = Pin(
            id=1, created_at=datetime.datetime.now() - datetime.timedelta(hours=1))
        self.activity = FakeActivity(
            1, LoveVerb, self.pin, 1, datetime.datetime.now(), {})
        self.feedly.flush()

    @implementation
    def test_add_user_activity(self):
        user_id = 42
        assert self.feedly.get_user_feed(
            user_id).count() == 0, 'the test feed is not empty'

        with patch.object(self.feedly, 'get_user_follower_ids', return_value=[]) as get_user_follower_ids:
            self.feedly.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id)

        assert self.feedly.get_user_feed(user_id).count() == 1

    @implementation
    def test_add_remove_user_activity(self):
        user_id = 42
        assert self.feedly.get_user_feed(
            user_id).count() == 0, 'the test feed is not empty'

        with patch.object(self.feedly, 'get_user_follower_ids', return_value=[]) as get_user_follower_ids:
            self.feedly.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id)
        assert self.feedly.get_user_feed(user_id).count() == 1

        with patch.object(self.feedly, 'get_user_follower_ids', return_value=[]) as get_user_follower_ids:
            self.feedly.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id)
        assert self.feedly.get_user_feed(user_id).count() == 1

    @implementation
    def test_add_user_activity_fanout(self):
        user_id = 42
        followers = [1, 2, 3]
        assert self.feedly.get_user_feed(
            user_id).count() == 0, 'the test feed is not empty'

        for follower in followers:
            assert self.feedly.get_user_feed(follower).count() == 0

        with patch.object(self.feedly, 'get_user_follower_ids', return_value=followers) as get_user_follower_ids:
            self.feedly.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id)

        assert self.feedly.get_user_feed(user_id).count() == 1

        for follower in followers:
            assert self.feedly.get_user_feed(follower).count() == 0
            for f in self.feedly.get_feeds(follower):
                assert f.count() == 1

    @implementation
    def test_follow_unfollow_user(self):
        target_user_id = 17
        follower_user_id = 42

        with patch.object(self.feedly, 'get_user_follower_ids', return_value=[]) as get_user_follower_ids:
            self.feedly.add_user_activity(target_user_id, self.activity)
            get_user_follower_ids.assert_called_with(target_user_id)
        assert self.feedly.get_user_feed(target_user_id).count() == 1

        self.feedly.follow_user(follower_user_id, target_user_id)
        
        for f in self.feedly.get_feeds(follower_user_id):
            assert f.count() == 1, 'follow did not copy any activities'

        self.feedly.unfollow_user(follower_user_id, target_user_id)
        for f in self.feedly.get_feeds(follower_user_id):
            assert f.count() == 0, 'follow did not remove activities from followings'
