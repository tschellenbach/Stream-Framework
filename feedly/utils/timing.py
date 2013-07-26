import time


class timer(object):

    def __init__(self):
        self.times = [time.time()]
        self.total = 0.
        self.next()

    def next(self):
        times = self.times
        times.append(time.time())
        delta = times[-1] - times[-2]
        self.total += delta
        return delta
