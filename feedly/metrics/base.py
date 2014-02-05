class NoopTimer(object):

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwds):
        pass

class Metrics(object):

    def fanout_timer(self):
        return NoopTimer()

    def feed_reads_timer(self):
        return NoopTimer()

    def on_fanout(self):
        pass

    def on_activity_published(self):
        pass

    def on_activity_removed(self):
        pass
