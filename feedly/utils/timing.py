import time


class timer(object):
    def __init__(self):
        self.times = [time.time()]
        self.total = 0.
        self.next()

    def __iter__(self):
        while True:
            yield self.next()

    def next(self):
        times = self.times
        times.append(time.time())
        delta = times[-1] - times[-2]
        self.total += delta
        return delta

    def get_avg(self, default=None):
        if self.times:
            return self.total / len(self.times)
        else:
            return default

    avg = property(get_avg)