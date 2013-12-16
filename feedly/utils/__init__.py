import collections
from datetime import datetime
from feedly.exceptions import DuplicateActivityException
import functools
import itertools
import logging
import time


logger = logging.getLogger(__name__)

def chunks(iterable, n=10000):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def datetime_to_epoch(dt):
    return time.mktime(dt.timetuple())


def epoch_to_datetime(time_):
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


class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated).
   '''

   def __init__(self, func):
      self.func = func
      self.cache = {}

   def __call__(self, *args):
      if not isinstance(args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value

   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__

   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)
