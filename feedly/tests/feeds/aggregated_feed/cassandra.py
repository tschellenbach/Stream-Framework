from feedly.feeds.aggregated_feed import CassandraAggregatedFeed
from feedly.tests.feeds.aggregated_feed.base import TestAggregatedFeed


class TestCassandraAggregatedFeed(TestAggregatedFeed):
    feed_cls = CassandraAggregatedFeed

    activity_storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['cassandra.localhost'],
        'column_family_name': 'activity'
    }

    timeline_storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['cassandra.localhost'],
        'column_family_name': 'timeline'
    }
