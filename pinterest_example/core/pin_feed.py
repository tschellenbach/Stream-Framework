from feedly.feeds.redis import RedisFeed
from feedly.feeds.cassandra import Feed as CassandraFeed
from feedly.feeds.aggregated_feed.redis import RedisAggregatedFeed
from feedly.aggregators.base import FashiolistaAggregator
from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed


class PinFeed(RedisFeed):
    pass


class AggregatedPinFeed(CassandraAggregatedFeed):
    aggregator_class = FashiolistaAggregator


class CassandraPinFeed(CassandraFeed):
    pass
