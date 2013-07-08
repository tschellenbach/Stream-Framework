from feedly.feeds.redis import RedisFeed
from feedly.feeds.cassandra import Feed as CassandraFeed


class PinFeed(RedisFeed):
    pass


class CassandraPinFeed(CassandraFeed):
    pass