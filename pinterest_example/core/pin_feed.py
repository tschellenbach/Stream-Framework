from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.redis import RedisFeed
from feedly.feeds.aggregated_feed.redis import RedisAggregatedFeed


class PinFeed(RedisFeed):
    key_format = 'feed:normal:%(user_id)s'


class AggregatedPinFeed(RedisAggregatedFeed):
    aggregator_class = RecentVerbAggregator
    key_format = 'feed:aggregated:%(user_id)s'


class UserPinFeed(PinFeed):
    key_format = 'feed:user:%(user_id)s'
