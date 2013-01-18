import functools
from feedly.exceptions import DuplicateActivityException
import logging

logger = logging.getLogger(__name__)


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


def is_active(switch_name):
    from django.conf import settings
    from gargoyle import gargoyle
    switch_enabled = gargoyle.is_active(switch_name)
    enabled = switch_enabled or settings.TEST_FEEDLY
    return enabled


def warn_on_error(f, exceptions):
    import sys
    assert exceptions
    assert isinstance(exceptions, tuple)

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except exceptions, e:
            logger.warn(unicode(e), exc_info=sys.exc_info(), extra={
                'data': {
                    'body': unicode(e),
                }
            })
    return wrapper


def warn_on_duplicate(f):
    exceptions = (DuplicateActivityException,)
    return warn_on_error(f, exceptions)


def make_list_unique(sequence, marker_function=None):
    '''
    Makes items in a list unique
    Performance based on this blog post:
    http://www.peterbe.com/plog/uniqifiers-benchmark
    '''
    seen = {}
    result = []
    for item in sequence:
        # gets the marker
        marker = item
        if marker_function is not None:
            marker = marker_function(item)
        # if no longer unique make unique
        if marker in seen:
            continue
        seen[marker] = True
        result.append(item)
    return result
