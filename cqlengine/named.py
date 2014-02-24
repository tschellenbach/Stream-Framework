from cqlengine.exceptions import CQLEngineException
from cqlengine.query import AbstractQueryableColumn, SimpleQuerySet

from cqlengine.query import DoesNotExist as _DoesNotExist
from cqlengine.query import MultipleObjectsReturned as _MultipleObjectsReturned


class QuerySetDescriptor(object):

    """
    returns a fresh queryset for the given model
    it's declared on everytime it's accessed
    """

    def __get__(self, obj, model):
        """ :rtype: ModelQuerySet """
        if model.__abstract__:
            raise CQLEngineException(
                'cannot execute queries against abstract models')
        return SimpleQuerySet(obj)

    def __call__(self, *args, **kwargs):
        """
        Just a hint to IDEs that it's ok to call this

        :rtype: ModelQuerySet
        """
        raise NotImplementedError


class NamedColumn(AbstractQueryableColumn):

    """
    A column that is not coupled to a model class, or type
    """

    def __init__(self, name):
        self.name = name

    def _get_column(self):
        return self

    @property
    def cql(self):
        return self.get_cql()

    def get_cql(self):
        return '"{}"'.format(self.name)


class NamedTable(object):

    """
    A Table that is not coupled to a model class
    """

    __abstract__ = False

    objects = QuerySetDescriptor()

    class DoesNotExist(_DoesNotExist):
        pass

    class MultipleObjectsReturned(_MultipleObjectsReturned):
        pass

    def __init__(self, keyspace, name):
        self.keyspace = keyspace
        self.name = name

    def column(self, name):
        return NamedColumn(name)

    def column_family_name(self, include_keyspace=True):
        """
        Returns the column family name if it's been defined
        otherwise, it creates it from the module and class name
        """
        if include_keyspace:
            return '{}.{}'.format(self.keyspace, self.name)
        else:
            return self.name

    def _get_column(self, name):
        """
        Returns the column matching the given name

        :rtype: Column
        """
        return self.column(name)

    # def create(self, **kwargs):
    #     return self.objects.create(**kwargs)

    def all(self):
        return self.objects.all()

    def filter(self, *args, **kwargs):
        return self.objects.filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.objects.get(*args, **kwargs)


class NamedKeyspace(object):

    """
    A keyspace
    """

    def __init__(self, name):
        self.name = name

    def table(self, name):
        """
        returns a table descriptor with the given
        name that belongs to this keyspace
        """
        return NamedTable(self.name, name)
