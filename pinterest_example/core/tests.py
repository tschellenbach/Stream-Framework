from core.models import Follow, Pin
from core.utils.request import RequestMock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.testcases import TestCase
from pinterest_example.core.pin_feedly import feedly
import json
import os


def absolute_path(path):
    return os.path.join(settings.BASE_DIR, path)


class BaseTestCase(TestCase):
    fixtures = map(
        absolute_path, ['core/fixtures/testdata.json', 'core/fixtures/board.json', 'core/fixtures/items.json'])

    def setUp(self):
        TestCase.setUp(self)

        self.bogus_user = bogus_user = get_user_model().objects.get(
            username='bogus')
        self.bogus_user2 = bogus_user2 = get_user_model().objects.get(
            username='bogus2')
        # start by resetting the feeds
        for u in [self.bogus_user, self.bogus_user2]:
            user_feed = feedly.get_user_feed(u.id)
            user_feed.delete()
            for name, feed in feedly.get_feeds(u.id).items():
                feed.delete()

        # login the user
        rf = RequestMock()
        self.rf = rf
        self.client = Client()
        self.auth_client = Client()
        self.auth_client2 = Client()
        auth_response = self.auth_client.login(
            username='bogus', password='bogus')
        self.assertTrue(auth_response)
        auth_response = self.auth_client2.login(
            username='bogus2', password='bogus')
        self.assertTrue(auth_response)


class PinTest(BaseTestCase):

    def test_pin(self):
        data = dict(
            message='my awesome pin',
            item=1,
            board_name='my favourite things',
            influencer=1,
        )
        pin_url = reverse('pin') + '?ajax=1'
        response = self.client.post(pin_url, data)
        self.assertEqual(response.status_code, 302)
        pin_response = self.auth_client.post(pin_url, data)
        self.assertEqual(pin_response.status_code, 200)
        
        response_data = json.loads(pin_response.content)
        self.assertTrue(response_data['pin'])
        self.assertTrue(response_data['pin']['id'])
        
    def test_unpin(self):
        data = dict(
            message='my awesome pin',
            item=1,
            board_name='my favourite things',
            influencer=1,
        )
        pin_url = reverse('pin') + '?ajax=1'
        response = self.client.post(pin_url, data)
        self.assertEqual(response.status_code, 302)
        pin_response = self.auth_client.post(pin_url, data)
        self.assertEqual(pin_response.status_code, 200)
        response_data = json.loads(pin_response.content)
        self.assertTrue(response_data['pin'])
        self.assertTrue(response_data['pin']['id'])
        data['remove'] = 1
        response = self.auth_client.post(pin_url, data)
        pins = list(Pin.objects.filter(item=1, user=self.bogus_user)[:4])
        assert pins == []


class FollowTest(BaseTestCase):

    def test_follow(self):
        data = dict(
            target=2,
        )
        follow_url = reverse('follow')
        response = self.client.post(follow_url, data)
        self.assertEqual(response.status_code, 302)
        follow_response = self.auth_client.post(follow_url, data)
        self.assertEqual(follow_response.status_code, 200)
        response_data = json.loads(follow_response.content)
        self.assertTrue(response_data['follow'])
        self.assertTrue(response_data['follow']['id'])

    def test_unfollow(self):
        data = dict(
            target=2,
        )
        follow_url = reverse('follow')
        response = self.client.post(follow_url, data)
        self.assertEqual(response.status_code, 302)
        follow_response = self.auth_client.post(follow_url, data)
        self.assertEqual(follow_response.status_code, 200)
        response_data = json.loads(follow_response.content)
        self.assertTrue(response_data['follow'])
        self.assertTrue(response_data['follow']['id'])
        data['remove'] = 1
        response = self.auth_client.post(follow_url, data)
        follows = list(Follow.objects.filter(
            target=2, user=self.bogus_user)[:4])
        assert follows == []


class SimpleViewTest(BaseTestCase):

    def test_trending(self):
        url = reverse('trending')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_feed(self):
        url = reverse('feed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        url = reverse('profile', args=['bogus'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, 200)
        
        
class FeedlyViewTest(BaseTestCase):
    def pin_in_feed(self, pin, auth_client):
        # this should be in the feed of bogus2
        feed_url = reverse('feed')
        response = auth_client.get(feed_url)
        feed_pins = response.context['feed_pins']
        present_in_feed = False
        pin_ids = [f.object_id for f in feed_pins]
        if feed_pins and pin.id in pin_ids:
            present_in_feed = True

        # now the aggregated feed
        aggregated_feed_url = reverse('aggregated_feed')
        response = auth_client.get(aggregated_feed_url)
        feed_pins = response.context['feed_pins']
        present_in_aggregated_feed = False
        pin_ids = sum([a.object_ids for a in feed_pins], [])
        if feed_pins and pin.id in pin_ids:
            present_in_aggregated_feed = True
            
        return present_in_feed, present_in_aggregated_feed
    
    def pin_in_profile(self, pin):
        profile_url = reverse('profile', args=[self.bogus_user.username])
        response = self.auth_client.get(profile_url)
        pins = response.context['profile_pins']
        present = False
        if pins and pins[0].object_id == pin.id:
            present = True
        return present
    
    def setup_bogus2_pins(self):
        # create 4 pins for bogus2
        for x in range(1, 4):
            data = dict(
                message='my awesome pin',
                item=x,
                board_name='my favourite things',
                influencer=1,
            )
            pin_url = reverse('pin') + '?ajax=1'
            self.auth_client2.post(pin_url, data)
    
    def test_pin_flow(self):
        '''
        Verify that a pin from bogus shows up on the feeds of
        bogus2
        '''
        # setup the pin for bogus
        data = dict(
            message='my awesome pin',
            item=2,
            board_name='my favourite things',
            influencer=1,
        )
        pin_url = reverse('pin') + '?ajax=1'
        self.auth_client.post(pin_url, data)
        last_pin = Pin.objects.all().order_by('-id')[:1][0]
        profile_pin = self.pin_in_profile(last_pin)
        self.assertTrue(profile_pin)
        feed, aggregated = self.pin_in_feed(last_pin)
        self.assertTrue(feed)
        self.assertTrue(aggregated)

        # now test removing that pin
        data['remove'] = 1
        self.auth_client.post(pin_url, data)
        profile_pin = self.pin_in_profile(last_pin)
        self.assertFalse(profile_pin)
        feed, aggregated = self.pin_in_feed(last_pin)
        self.assertFalse(feed)
        self.assertFalse(aggregated)
        
    def test_follow_flow(self):
        '''
        Bogus follows bogus2, which has 2 pins
        These pins should show up on the feed page of bogus
        
        After unfollowing bogus2 these pins should be gone
        '''
        # setup the pins for bogus2
        self.setup_bogus2_pins()
        pins = list(Pin.objects.filter(user_id=self.bogus_user2.id)[:3])
        self.assertTrue(pins)
        # follow bogus2
        data = dict(
            target=self.bogus_user2.id,
        )
        follow_url = reverse('follow')
        self.auth_client.post(follow_url, data)
        
        # verify that the pins are in the feed
        for pin in pins:
            feed, aggregated = self.pin_in_feed(pin, auth_client=self.auth_client)
            self.assertTrue(feed)
            self.assertTrue(aggregated)
            
        # unfollow bogus2
        data['remove'] = 1
        self.auth_client.post(follow_url, data)
        
        # verify that the pins are not there
        for pin in pins:
            feed, aggregated = self.pin_in_feed(pin, auth_client=self.auth_client)
            self.assertFalse(feed)
            self.assertFalse(aggregated)
