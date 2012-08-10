from feedly.tests import BaseFeedlyTestCase
from framework.utils.test.test_decorators import needs_love
from feedly.feed_managers.love_feedly import LoveFeedly
import datetime
import unittest


class BaseBenchMarkTest(unittest.TestCase):
    def setUp(self):
        self.start_time = datetime.datetime.now()

    def tearDown(self):
        now = datetime.datetime.now()
        delta = now - self.start_time
        print 'Time taken', delta.seconds


class IOBenchMarkTest(BaseBenchMarkTest):
    def test_write_performance(self):
        return
        from entity.models import Love
        feedly = LoveFeedly()
        love = Love.objects.filter(user=self.bogus_user)[:10][0]
        activity = feedly.create_love_activity(love)
        feeds = feedly.add_love(love)
        
    def test_read_performance(self):
        return
        from user.models import Profile
        feed_length = 24 * 3
        number_of_profiles = 10
        profiles = Profile.objects.all()[:number_of_profiles]
        profiles = list(profiles)
        
        def test_feed_performance(message_format, delete=False):
            #start the db version of the test
            start_time = datetime.datetime.now()
            for profile in profiles:
                feed = profile.get_feed()
                if delete:
                    feed.delete()
                results = feed[:feed_length]
                print profile.user, feed.count()
            now = datetime.datetime.now()
            delta = now - start_time
            print message_format % delta.seconds
            
        test_feed_performance('Database reads took: %s', delete=True)
        #make sure we don't run queries
        with self.assertNumQueries(0):
            test_feed_performance('Redis reads took: %s', delete=False)
