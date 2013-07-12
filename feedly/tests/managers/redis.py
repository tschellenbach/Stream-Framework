from feedly.tests.managers.base import BaseFeedlyTest
from feedly.feeds.redis import RedisFeed
import pytest


@pytest.mark.usefixtures("redis_reset")
class RedisFeedlyTest(BaseFeedlyTest):
    feed_class = RedisFeed
