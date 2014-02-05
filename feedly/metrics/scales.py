from feedly.metrics.base import Metrics
from greplin import scales


class ScalesMetrics(Metrics):


    def __init__(self, metric_namespace='/feedly'):

        self.stats = scales.collection(metric_namespace,
            scales.PmfStat('fanout_timer'),
            scales.PmfStat('feed_reads_timer'),
            scales.IntStat('fanouts'),
            scales.IntStat('activities_published'),
            scales.IntStat('activities_removed')
    )

    def fanout_timer(self):
      return self.stats.fanout_timer.time()

    def feed_reads_timer(self):
      return self.stats.feed_reads_timer.time()

    def on_fanout(self):
      self.stats.fanouts += 1

    def on_activity_published(self):
      self.stats.activities_published += 1

    def on_activity_removed(self):
      self.stats.activities_removed += 1
