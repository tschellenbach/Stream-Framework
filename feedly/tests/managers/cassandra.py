from feedly.tests.managers.base import BaseFeedlyTest
from feedly.feeds.cassandra import Feed
import pytest


@pytest.mark.usefixtures("cassandra_reset")
class CassandraTest(BaseFeedlyTest):
    feed_class = Feed

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
