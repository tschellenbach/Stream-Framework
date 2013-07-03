import unittest
from feedly.feeds.base import BaseFeed

class TestBaseFeed(unittest.TestCase):
    feed_cls = BaseFeed

    def setUp(self):
        self.user_id = 42

    def test_format_key(self):
        self.feed = BaseFeed(self.user_id, {}, {})
        assert self.feed.key == self.feed.key_format % self.user_id
