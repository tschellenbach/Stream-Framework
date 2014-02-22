from datetime import datetime
from uuid import uuid1

from cqlengine.exceptions import ValidationError


class QueryValue(object):

    """
    Base class for query filter values. Subclasses of these classes can
    be passed into .filter() keyword args
    """

    _cql_string = '%({})s'

    def __init__(self, value, identifier=None):
        self.value = value
        self.identifier = uuid1().hex if identifier is None else identifier

    def get_cql(self):
        return self._cql_string.format(self.identifier)

    def get_value(self):
        return self.value

    def get_dict(self, column):
        return {self.identifier: self.get_value()}

    @property
    def cql(self):
        return self.get_cql()


class BaseQueryFunction(QueryValue):

    """
    Base class for filtering functions. Subclasses of these classes can
    be passed into .filter() and will be translated into CQL functions in
    the resulting query
    """


class MinTimeUUID(BaseQueryFunction):

    """
    return a fake timeuuid corresponding to the smallest possible timeuuid for the given timestamp

    http://cassandra.apache.org/doc/cql3/CQL.html#timeuuidFun
    """

    _cql_string = 'MinTimeUUID(:{})'

    def __init__(self, value):
        """
        :param value: the time to create a maximum time uuid from
        :type value: datetime
        """
        if not isinstance(value, datetime):
            raise ValidationError('datetime instance is required')
        super(MinTimeUUID, self).__init__(value)

    def get_value(self):
        epoch = datetime(1970, 1, 1)
        return long((self.value - epoch).total_seconds() * 1000)

    def get_dict(self, column):
        return {self.identifier: self.get_value()}


class MaxTimeUUID(BaseQueryFunction):

    """
    return a fake timeuuid corresponding to the largest possible timeuuid for the given timestamp

    http://cassandra.apache.org/doc/cql3/CQL.html#timeuuidFun
    """

    _cql_string = 'MaxTimeUUID(%({})s)'

    def __init__(self, value):
        """
        :param value: the time to create a minimum time uuid from
        :type value: datetime
        """
        if not isinstance(value, datetime):
            raise ValidationError('datetime instance is required')
        super(MaxTimeUUID, self).__init__(value)

    def get_value(self):
        epoch = datetime(1970, 1, 1)
        return long((self.value - epoch).total_seconds() * 1000)

    def get_dict(self, column):
        return {self.identifier: self.get_value()}


class Token(BaseQueryFunction):

    """
    compute the token for a given partition key

    http://cassandra.apache.org/doc/cql3/CQL.html#tokenFun
    """

    def __init__(self, *values):
        if len(values) == 1 and isinstance(values[0], (list, tuple)):
            values = values[0]
        super(Token, self).__init__(values, [uuid1().hex for i in values])

    def get_dict(self, column):
        items = zip(self.identifier, self.value, column.partition_columns)
        return dict(
            (id, val) for id, val, col in items
        )

    def get_cql(self):
        token_args = ', '.join(':{}'.format(id) for id in self.identifier)
        return "token({})".format(token_args)
