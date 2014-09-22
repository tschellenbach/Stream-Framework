from __future__ import absolute_import
from stream_framework.metrics.base import Metrics
import statsd


class Timer(object):

    def __init__(self, metric_name):
        self.metric_name = metric_name

    def __enter__(self):
        self.timer = statsd.Timer(self.metric_name)
        self.timer.start()

    def __exit__(self, *args, **kwds):
        self.timer.stop()


class StatsdMetrics(Metrics):

    def __init__(self, host='localhost', port=8125, prefix='stream_framework'):
        statsd.Connection.set_defaults(host=host, port=port)
        self.prefix = prefix

    def fanout_timer(self, feed_class):
        return Timer('%s.%s.fanout_latency' % (self.prefix, feed_class.__name__))

    def feed_reads_timer(self, feed_class):
        return Timer('%s.%s.read_latency' % (self.prefix, feed_class.__name__))

    def on_feed_read(self, feed_class, activities_count):
        counter = statsd.Counter(
            '%s.%s.reads' % (self.prefix, feed_class.__name__))
        counter += activities_count

    def on_feed_write(self, feed_class, activities_count):
        counter = statsd.Counter(
            '%s.%s.writes' % (self.prefix, feed_class.__name__))
        counter += activities_count

    def on_feed_remove(self, feed_class, activities_count):
        counter = statsd.Counter(
            '%s.%s.deletes' % (self.prefix, feed_class.__name__))
        counter += activities_count

    def on_fanout(self, feed_class, operation, activities_count=1):
        metric = (self.prefix, feed_class.__name__, operation.__name__)
        counter = statsd.Counter('%s.%s.fanout.%s' % metric)
        counter += activities_count

    def on_activity_published(self):
        counter = statsd.Counter('%s.activities.published' % self.prefix)
        counter += 1

    def on_activity_removed(self):
        counter = statsd.Counter('%s.activities.removed' % self.prefix)
        counter += 1
