from django.test.testcases import TestCase
from core.utils.request import RequestMock
from django.core.urlresolvers import reverse
from django.test.client import Client
import json


class BaseTestCase(TestCase):
    fixtures = ['core/fixtures/testdata.json', 'core/fixtures/board.json']
    
    def setUp(self):
        TestCase.setUp(self)
        rf = RequestMock()
        self.rf = rf
        self.client = Client()
        self.auth_client = Client()
        auth_response = self.auth_client.login(username='bogus', password='bogus')
        self.assertTrue(auth_response)
        

class PinTest(BaseTestCase):
    def test_pin(self):
        data = dict(
            message='my awesome pin',
            item=1,
            board=1,
            influencer=1,
        )
        pin_url = reverse('pin')
        response = self.client.post(pin_url, data)
        self.assertEqual(response.status_code, 302)
        pin_response = self.auth_client.post(pin_url, data)
        self.assertEqual(pin_response.status_code, 200)
        self.assertEqual(json.loads(pin_response.content), dict(pin=dict(id=1)))


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
        self.assertEqual(json.loads(follow_response.content), dict(follow=dict(id=1)))
        
        
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