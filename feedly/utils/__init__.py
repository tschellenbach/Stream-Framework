import functools
from feedly.exceptions import DuplicateActivityException
import logging
import itertools

logger = logging.getLogger(__name__)


def chunks(iterable, n=10000):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def datetime_to_epoch(dt):
    import time
    time_ = time.mktime(dt.timetuple())
    return time_


def epoch_to_datetime(time_):
    from datetime import datetime
    return datetime.fromtimestamp(time_)


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
