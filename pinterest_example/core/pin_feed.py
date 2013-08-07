from feedly.aggregators.base import RecentVerbAggregator
from feedly.feeds.cassandra import CassandraFeed
from feedly.feeds.redis import RedisFeed
from feedly.feeds.aggregated_feed.redis import RedisAggregatedFeed
from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed


class PinFeed(CassandraFeed):
    key_format = 'feed:normal:%(user_id)s'


class AggregatedPinFeed(CassandraAggregatedFeed):
    aggregator_class = RecentVerbAggregator
    key_format = 'feed:aggregated:%(user_id)s'


class UserPinFeed(PinFeed):
    key_format = 'feed:user:%(user_id)s'
