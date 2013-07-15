from feedly.aggregators.base import FashiolistaAggregator
from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed
from feedly.feeds.cassandra import CassandraFeed
from feedly.feeds.redis import RedisFeed


class PinFeed(RedisFeed):
    pass


class AggregatedPinFeed(CassandraAggregatedFeed):
    aggregator_class = FashiolistaAggregator


class UserPinFeed(PinFeed):
    key_format = 'feed_%(user_id)s'


class CassandraPinFeed(CassandraFeed):
    pass
