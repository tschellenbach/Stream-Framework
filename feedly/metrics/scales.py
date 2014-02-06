from feedly.metrics.base import Metrics
from greplin import scales


class ScalesMetrics(Metrics):

    def __init__(self, metric_namespace='/feedly'):
        self.metric_namespace = metric_namespace
        self.stats = scales.collection(metric_namespace,
            scales.IntStat('fanouts'),
            scales.IntStat('activities_published'),
            scales.IntStat('activities_removed'),
            scales.IntDictSumAggregationStat('feed_read_counter'),
            scales.IntDictSumAggregationStat('feed_write_counter'),
            scales.IntDictSumAggregationStat('feed_remove_counter')
        )

    def get_feed_timer(self, feed_class, name):
        path = '/'.join([self.metric_namespace, feed_class.__name__])
        collection = scales.collection(path, scales.PmfStat(name))
        return getattr(collection, name).time()

    def fanout_timer(self, feed_class):
        return self.get_feed_timer(feed_class, 'fanout_timer')

    def feed_reads_timer(self, feed_class):
        return self.get_feed_timer(feed_class, 'feed_reads_timer')

    def on_feed_read(self, feed_class, activities_count):
        self.stats.feed_read_counter[feed_class.__name__] += activities_count

    def on_feed_write(self, feed_class, activities_count):
        self.stats.feed_write_counter[feed_class.__name__] += activities_count

    def on_feed_remove(self, feed_class, activities_count):
        self.stats.feed_remove_counter[feed_class.__name__] += activities_count

    def on_fanout(self):
        self.stats.fanouts += 1

    def on_activity_published(self):
        self.stats.activities_published += 1

    def on_activity_removed(self):
        self.stats.activities_removed += 1
