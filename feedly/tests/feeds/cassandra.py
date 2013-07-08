from feedly.tests.feeds.base import TestBaseFeed
from feedly.feeds.cassandra import Feed
import pytest


@pytest.mark.usefixtures("cassandra_reset")
class CassandraBaseFeed(TestBaseFeed):
    feed_cls = Feed

    activity_storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['localhost'],
        'column_family_name': 'activity'
    }

    timeline_storage_options = {
        'keyspace_name': 'test_feedly',
        'hosts': ['localhost'],
        'column_family_name': 'timeline'
    }
