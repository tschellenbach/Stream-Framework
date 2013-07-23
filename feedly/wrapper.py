from mock import MagicMock
from copy import copy


class FeedResultsWrapper(object):
    """
    wraps a sorted set wrapper to work with SmartQuerysetPaginator
    this supports only few of the maaaaany features

    pk desc is the ONLY way you can sort the feed

    """

    def __init__(self, feed, *wrappers):
        self.__dict__ = feed.__dict__
        self.wrappers = wrappers
        self.feed = feed
        self.offset = 0

    class query:
        order_by = ('-pk', )

    class model:
        class _meta:
            @classmethod
            def get_field(*args, **kwargs):
                pk_field = MagicMock()
                pk_field.configure_mock(unique=True, name='pk')
                return pk_field

    def filter(self, pk__lt=None, pk__lte=None, pk__gt=None, pk__gte=None):
        _self = copy(self)
        left_most_element = pk__lt or pk__lte
        right_most_element = pk__gt or pk__gte

        if left_most_element is not None:
            _self.offset += self.feed.index_of(long(left_most_element))
    
        if right_most_element is not None:
            _self.offset -= self.feed.index_of(long(right_most_element))

        if pk__lt is not None:
            _self.offset -= 1

        if pk__gt is not None:
            _self.offset -= 1
            
        return _self

    def order_by(self, *args, **kwargs):
        if '-pk' in args or '-id' in args:
            return self
        raise TypeError('cant change order of feeds')

    def values_list(self, attrname, flat=False):
        '''

        add supports for this two usecases
        values_list('pk')
        values_list('id')

        '''
        assert attrname in ('id', 'pk') , 'only id and pk are supported'

        def _values_list(results):
            for i, activity in enumerate(results):
                value = activity.serialization_id
                if not flat:
                    value = [value]
                results[i] = value
            return results

        _self = FeedResultsWrapper(self.feed, _values_list)
        _self.wrappers = (_values_list, )
        return _self

    def __len__(self):
        return self.feed.__len__()

    def __getitem__(self, k):
        step = None
        if hasattr(k, 'step'):
            step = k.step

        start = k.start or 0 + self.offset
        stop = k.stop
        if stop is not None:
            stop += self.offset
        feed_slice = slice(start, stop)
        results = self.feed.__getitem__(feed_slice)
        for wrapper in self.wrappers:
            results = wrapper(results)
        return results[:][::step]

    def wrap(self, *wrappers):
        self.wrappers = getattr(self, 'wrappers', ()) + wrappers
        return self