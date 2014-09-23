class NoopTimer(object):

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwds):
        pass


class Metrics(object):

    def __init__(self, *args, **kwargs):
        pass

    def fanout_timer(self, feed_class):
        return NoopTimer()

    def feed_reads_timer(self, feed_class):
        return NoopTimer()

    def on_feed_read(self, feed_class, activities_count):
        pass

    def on_feed_remove(self, feed_class, activities_count):
        pass

    def on_feed_write(self, feed_class, activities_count):
        pass

    def on_fanout(self, feed_class, operation, activities_count=1):
        pass

    def on_activity_published(self):
        pass

    def on_activity_removed(self):
        pass
