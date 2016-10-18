import pytest


@pytest.fixture(autouse=True)
def celery_eager():
    from celery import current_app
    current_app.conf.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


@pytest.fixture
def redis_reset():
    import redis
    redis.Redis().flushall()


@pytest.fixture
def cassandra_reset():
    from stream_framework.feeds.cassandra import CassandraFeed
    from stream_framework.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed
    from cassandra.cqlengine.management import create_keyspace_simple, sync_table
    from stream_framework import settings
    create_keyspace_simple(settings.STREAM_DEFAULT_KEYSPACE, 1)
    aggregated_timeline = CassandraAggregatedFeed.get_timeline_storage()
    timeline = CassandraFeed.get_timeline_storage()
    sync_table(aggregated_timeline.model)
    sync_table(timeline.model)
