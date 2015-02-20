import datetime
from stream_framework.feed_managers.base import Manager
from stream_framework.tests.utils import Pin
from stream_framework.tests.utils import FakeActivity
from stream_framework.verbs.base import Love as LoveVerb
from mock import patch
import unittest
import copy
from functools import partial


def implementation(meth):
    def wrapped_test(self, *args, **kwargs):
        if self.__class__ == BaseManagerTest:
            raise unittest.SkipTest('only test this on actual implementations')
        return meth(self, *args, **kwargs)
    return wrapped_test


class BaseManagerTest(unittest.TestCase):
    manager_class = Manager

    def setUp(self):
        self.manager = self.manager_class()
        self.actor_id = 42
        self.pin = Pin(
            id=1, created_at=datetime.datetime.now() - datetime.timedelta(hours=1))
        self.activity = FakeActivity(
            self.actor_id, LoveVerb, self.pin, 1, datetime.datetime.now(), {})

        if self.__class__ != BaseManagerTest:
            for user_id in list(range(1, 4)) + [17, 42, 44]:
                self.manager.get_user_feed(user_id).delete()
                for feed in self.manager.get_feeds(user_id).values():
                    feed.delete()

    @implementation
    def test_add_user_activity(self):
        assert self.manager.get_user_feed(
            self.actor_id).count() == 0, 'the test feed is not empty'

        with patch.object(self.manager, 'get_user_follower_ids', return_value={None: [1]}) as get_user_follower_ids:
            self.manager.add_user_activity(self.actor_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id=self.actor_id)

        assert self.manager.get_user_feed(self.actor_id).count() == 1
        for feed in self.manager.get_feeds(1).values():
            assert feed.count() == 1

    @implementation
    def test_batch_import(self):
        assert self.manager.get_user_feed(
            self.actor_id).count() == 0, 'the test feed is not empty'

        with patch.object(self.manager, 'get_user_follower_ids', return_value={None: [1]}) as get_user_follower_ids:
            activities = [self.activity]
            self.manager.batch_import(self.actor_id, activities, 10)
            get_user_follower_ids.assert_called_with(user_id=self.actor_id)

        assert self.manager.get_user_feed(self.actor_id).count() == 1
        for feed in self.manager.get_feeds(1).values():
            assert feed.count() == 1

    @implementation
    def test_batch_import_errors(self):
        activities = []
        # this should return without trouble
        self.manager.batch_import(self.actor_id, activities, 10)

        # batch import with activities from different users should give an
        # error
        activity = copy.deepcopy(self.activity)
        activity.actor_id = 10
        with patch.object(self.manager, 'get_user_follower_ids', return_value={None: [1]}):
            batch = partial(
                self.manager.batch_import, self.actor_id, [activity], 10)
            self.assertRaises(ValueError, batch)

    @implementation
    def test_add_remove_user_activity(self):
        user_id = 42
        assert self.manager.get_user_feed(
            user_id).count() == 0, 'the test feed is not empty'

        with patch.object(self.manager, 'get_user_follower_ids', return_value={None: [1]}) as get_user_follower_ids:
            self.manager.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id=user_id)
        assert self.manager.get_user_feed(user_id).count() == 1

        with patch.object(self.manager, 'get_user_follower_ids', return_value={None: [1]}) as get_user_follower_ids:
            self.manager.remove_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id=user_id)
        assert self.manager.get_user_feed(user_id).count() == 0

    @implementation
    def test_add_user_activity_fanout(self):
        user_id = 42
        followers = {None: [1, 2, 3]}
        assert self.manager.get_user_feed(
            user_id).count() == 0, 'the test feed is not empty'

        for follower in followers.values():
            assert self.manager.get_user_feed(follower).count() == 0

        with patch.object(self.manager, 'get_user_follower_ids', return_value=followers) as get_user_follower_ids:
            self.manager.add_user_activity(user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id=user_id)

        assert self.manager.get_user_feed(user_id).count() == 1

        for follower in list(followers.values())[0]:
            assert self.manager.get_user_feed(follower).count() == 0
            for f in self.manager.get_feeds(follower).values():
                assert f.count() == 1

    @implementation
    def test_follow_unfollow_user(self):
        target_user_id = 17
        target2_user_id = 44
        follower_user_id = 42

        control_pin = Pin(
            id=2, created_at=datetime.datetime.now() - datetime.timedelta(hours=1))
        control_activity = FakeActivity(
            target_user_id, LoveVerb, control_pin, 2, datetime.datetime.now(), {})

        with patch.object(self.manager, 'get_user_follower_ids', return_value={}) as get_user_follower_ids:
            self.manager.add_user_activity(target2_user_id, control_activity)
            self.manager.add_user_activity(target_user_id, self.activity)
            get_user_follower_ids.assert_called_with(user_id=target_user_id)

        # checks user feed is empty
        for f in self.manager.get_feeds(follower_user_id).values():
            self.assertEqual(f.count(), 0)

        self.manager.follow_user(follower_user_id, target2_user_id)

        # make sure one activity was pushed
        for f in self.manager.get_feeds(follower_user_id).values():
            self.assertEqual(f.count(), 1)

        self.manager.follow_user(follower_user_id, target_user_id)

        # make sure another one activity was pushed
        for f in self.manager.get_feeds(follower_user_id).values():
            self.assertEqual(f.count(), 2)

        self.manager.unfollow_user(
            follower_user_id, target_user_id, async=False)

        # make sure only one activity was removed
        for f in self.manager.get_feeds(follower_user_id).values():
            self.assertEqual(f.count(), 1)
            activity = f[:][0]
            assert activity.object_id == self.pin.id
