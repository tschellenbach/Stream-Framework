

def chunks(l, n=10000):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def datetime_to_epoch(dt):
    import time
    time_ = time.mktime(dt.timetuple())
    return time_


def datetime_to_desc_epoch(dt):
    return datetime_to_epoch(dt) * -1


def epoch_to_datetime(time_):
    from datetime import datetime
    return datetime.fromtimestamp(time_)


def time_desc():
    import time
    negative_time = time.time() * -1
    return negative_time


def time_asc():
    import time
    positive_time = time.time()
    return positive_time