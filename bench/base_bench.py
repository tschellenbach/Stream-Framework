import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ["DJANGO_SETTINGS_MODULE"] = "conf"
from feedly.utils.timing import timer
import logging
from feedly.activity import Activity
from feedly.feeds.cassandra import CassandraFeed
from feedly.feeds.aggregated_feed.cassandra import CassandraAggregatedFeed
from feedly.feed_managers.base import Feedly
from feedly.feed_managers.base import FanoutPriority
from feedly.verbs.base import Love
from optparse import OptionParser


logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(handler)


def parse_options():
    parser = OptionParser()
    parser.add_option('-l', '--log-level', default='warning',
                      help='logging level: debug, info, warning, or error')
    parser.add_option('-p', '--profile', action='store_true', dest='profile',
                      help='Profile the run')
    options, args = parser.parse_args()
    logger.setLevel(options.log_level.upper())
    return options, args


class FashiolistaFeed(CassandraFeed):
    timeline_cf_name = 'timeline_flat'
    key_format = 'feed:flat:%(user_id)s'
    max_length = 3600

    def trim(self, *args, **kwargs):
        pass


class UserFeed(CassandraFeed):
    timeline_cf_name = 'timeline_personal'
    key_format = 'feed:personal:%(user_id)s'
    max_length = 10 ** 6


class AggregatedFeed(CassandraAggregatedFeed):
    timeline_cf_name = 'timeline_aggregated'
    key_format = 'feed:aggregated:%(user_id)s'
    lock_format = 'feed:aggregated:lock:%(user_id)s'
    max_length = 2400
    merge_max_length = 1


class BenchFeedly(Feedly):
    feed_classes = {
        'aggregated': AggregatedFeed,
        'flat': FashiolistaFeed
    }
    user_feed_class = UserFeed
    follow_activity_limit = 360
    fanout_chunk_size = 100

    def add_entry(self, user_id, activity_id):
        verb = Love()
        activity = Activity(user_id, verb, activity_id)
        self.add_user_activity(user_id, activity)

    def get_user_follower_ids(self, user_id):
        active_follower_ids = range(100)
        return { FanoutPriority.HIGH: active_follower_ids }


manager = BenchFeedly()


def cassandra_setup():
    from cqlengine.management import create_table, create_keyspace
    aggregated_timeline = AggregatedFeed.get_timeline_storage()
    timeline = FashiolistaFeed.get_timeline_storage()
    user_timeline = UserFeed.get_timeline_storage()
    create_keyspace('test')
    create_table(aggregated_timeline.model)
    create_table(timeline.model)
    create_table(user_timeline.model)


def benchmark():
    benchmark_flat_feed()
    benchmark_aggregated_feed()


def benchmark_flat_feed():
    t = timer()
    manager.feed_classes = {'flat': FashiolistaFeed}
    manager.add_entry(1, 1)
    print "Benchmarking flat feed took: %0.2fs" % t.next()


def benchmark_aggregated_feed():
    t = timer()
    manager.feed_classes = {'aggregated': AggregatedFeed}
    manager.add_entry(1, 1)
    print "Benchmarking aggregated feed took: %0.2fs" % t.next()


if __name__ == '__main__':
    options, args = parse_options()
    cassandra_setup()
    benchmark()
