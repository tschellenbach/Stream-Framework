import copy
from datetime import datetime
from uuid import uuid4
from cqlengine import BaseContainerColumn, Map, columns
from cqlengine.columns import Counter
from cqlengine.connection import get_connection_pool
from cqlengine.connection import execute

from cqlengine.exceptions import CQLEngineException
from cqlengine.functions import QueryValue, Token
from cqlengine.utils import chunks


# CQL 3 reference:
# http://www.datastax.com/docs/1.1/references/cql/index

class QueryException(CQLEngineException):
    pass


class DoesNotExist(QueryException):
    pass


class MultipleObjectsReturned(QueryException):
    pass


class QueryOperatorException(QueryException):
    pass


class QueryOperator(object):
    # The symbol that identifies this operator in filter kwargs
    # ie: colname__<symbol>
    symbol = None

    # The comparator symbol this operator uses in cql
    cql_symbol = None

    QUERY_VALUE_WRAPPER = QueryValue

    def __init__(self, column, value):
        self.column = column
        self.value = value

        if isinstance(value, QueryValue):
            self.query_value = value
        else:
            self.query_value = self.QUERY_VALUE_WRAPPER(value)

        # perform validation on this operator
        self.validate_operator()
        self.validate_value()

    @property
    def cql(self):
        """
        Returns this operator's portion of the WHERE clause
        """
        return '{} {} {}'.format(self.column.cql, self.cql_symbol, self.query_value.cql)

    def validate_operator(self):
        """
        Checks that this operator can be used on the column provided
        """
        if self.symbol is None:
            raise QueryOperatorException(
                "{} is not a valid operator, use one with 'symbol' defined".format(
                    self.__class__.__name__
                )
            )
        if self.cql_symbol is None:
            raise QueryOperatorException(
                "{} is not a valid operator, use one with 'cql_symbol' defined".format(
                    self.__class__.__name__
                )
            )

    def validate_value(self):
        """
        Checks that the compare value works with this operator

        Doesn't do anything by default
        """
        pass

    def get_dict(self):
        """
        Returns this operators contribution to the cql.query arg dictionanry

        ie: if this column's name is colname, and the identifier is colval,
        this should return the dict: {'colval':<self.value>}
        SELECT * FROM column_family WHERE colname=:colval
        """
        return self.query_value.get_dict(self.column)

    @classmethod
    def get_operator(cls, symbol):
        if not hasattr(cls, 'opmap'):
            QueryOperator.opmap = {}

            def _recurse(klass):
                if klass.symbol:
                    QueryOperator.opmap[klass.symbol.upper()] = klass
                for subklass in klass.__subclasses__():
                    _recurse(subklass)
                pass
            _recurse(QueryOperator)
        try:
            return QueryOperator.opmap[symbol.upper()]
        except KeyError:
            raise QueryOperatorException(
                "{} doesn't map to a QueryOperator".format(symbol))

    # equality operator, used by tests

    def __eq__(self, op):
        return self.__class__ is op.__class__ and \
            self.column.db_field_name == op.column.db_field_name and \
            self.value == op.value

    def __ne__(self, op):
        return not (self == op)

    def __hash__(self):
        return hash(self.column.db_field_name) ^ hash(self.value)


class EqualsOperator(QueryOperator):
    symbol = 'EQ'
    cql_symbol = '='


class IterableQueryValue(QueryValue):

    def __init__(self, value):
        try:
            super(IterableQueryValue, self).__init__(
                value, [uuid4().hex for i in value])
        except TypeError:
            raise QueryException(
                "in operator arguments must be iterable, {} found".format(value))

    def get_dict(self, column):
        return dict((i, v) for (i, v) in zip(self.identifier, self.value))

    def get_cql(self):
        return '({})'.format(', '.join('%({})s'.format(i) for i in self.identifier))


class InOperator(EqualsOperator):
    symbol = 'IN'
    cql_symbol = 'IN'

    QUERY_VALUE_WRAPPER = IterableQueryValue


class GreaterThanOperator(QueryOperator):
    symbol = "GT"
    cql_symbol = '>'


class GreaterThanOrEqualOperator(QueryOperator):
    symbol = "GTE"
    cql_symbol = '>='


class LessThanOperator(QueryOperator):
    symbol = "LT"
    cql_symbol = '<'


class LessThanOrEqualOperator(QueryOperator):
    symbol = "LTE"
    cql_symbol = '<='


class AbstractQueryableColumn(object):

    """
    exposes cql query operators through pythons
    builtin comparator symbols
    """

    def _get_column(self):
        raise NotImplementedError

    def in_(self, item):
        """
        Returns an in operator

        used in where you'd typically want to use python's `in` operator
        """
        return InOperator(self._get_column(), item)

    def __eq__(self, other):
        return EqualsOperator(self._get_column(), other)

    def __gt__(self, other):
        return GreaterThanOperator(self._get_column(), other)

    def __ge__(self, other):
        return GreaterThanOrEqualOperator(self._get_column(), other)

    def __lt__(self, other):
        return LessThanOperator(self._get_column(), other)

    def __le__(self, other):
        return LessThanOrEqualOperator(self._get_column(), other)


class BatchType(object):
    Unlogged = 'UNLOGGED'
    Counter = 'COUNTER'


class BatchQuery(object):

    """
    Handles the batching of queries

    http://www.datastax.com/docs/1.2/cql_cli/cql/BATCH
    """

    def __init__(self, batch_type=None, timestamp=None):
        self.queries = []
        self.batch_type = batch_type
        if timestamp is not None and not isinstance(timestamp, datetime):
            raise CQLEngineException(
                'timestamp object must be an instance of datetime')
        self.timestamp = timestamp

    def add_query(self, query, params):
        self.queries.append((query, params))

    def execute(self):
        if len(self.queries) == 0:
            # Empty batch is a no-op
            return

        opener = 'BEGIN ' + \
            (self.batch_type + ' ' if self.batch_type else '') + ' BATCH'
        if self.timestamp:
            epoch = datetime(1970, 1, 1)
            ts = long((self.timestamp - epoch).total_seconds() * 1000)
            opener += ' USING TIMESTAMP {}'.format(ts)

        query_list = [opener]
        parameters = {}
        for query, params in self.queries:
            query_list.append('  ' + query)
            parameters.update(params)

        query_list.append('APPLY BATCH;')

        execute('\n'.join(query_list), parameters)

        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # don't execute if there was an exception
        if exc_type is not None:
            return
        self.execute()


class AbstractQuerySet(object):

    def __init__(self, model):
        super(AbstractQuerySet, self).__init__()
        self.model = model

        # Where clause filters
        self._where = []

        # ordering arguments
        self._order = []

        self._allow_filtering = False

        # CQL has a default limit of 10000, it's defined here
        # because explicit is better than implicit
        self._limit = 10000

        # see the defer and only methods
        self._defer_fields = []
        self._only_fields = []

        self._values_list = False
        self._flat_values_list = False

        # results cache
        self._con = None
        self._cur = None
        self._result_cache = None
        self._result_idx = None

        self._batch = None

    @property
    def column_family_name(self):
        return self.model.column_family_name()

    def __unicode__(self):
        return self._select_query()

    def __str__(self):
        return str(self.__unicode__())

    def __call__(self, *args, **kwargs):
        return self.filter(*args, **kwargs)

    def __deepcopy__(self, memo):
        clone = self.__class__(self.model)
        for k, v in self.__dict__.items():
            if k in ['_con', '_cur', '_result_cache', '_result_idx']:
                clone.__dict__[k] = None
            elif k == '_batch':
                # we need to keep the same batch instance across
                # all queryset clones, otherwise the batched queries
                # fly off into other batch instances which are never
                # executed, thx @dokai
                clone.__dict__[k] = self._batch
            else:
                clone.__dict__[k] = copy.deepcopy(v, memo)

        return clone

    def __len__(self):
        self._execute_query()
        return len(self._result_cache)

    #----query generation / execution----

    def _where_clause(self):
        """ Returns a where clause based on the given filter args """
        return ' AND '.join([f.cql for f in self._where])

    def _where_values(self):
        """ Returns the value dict to be passed to the cql query """
        values = {}
        for where in self._where:
            values.update(where.get_dict())
        return values

    def _get_select_statement(self):
        """ returns the select portion of this queryset's cql statement """
        raise NotImplementedError

    def _select_query(self):
        """
        Returns a select clause based on the given filter args
        """
        qs = [self._get_select_statement()]
        qs += ['FROM {}'.format(self.column_family_name)]

        if self._where:
            qs += ['WHERE {}'.format(self._where_clause())]

        if self._order:
            qs += ['ORDER BY {}'.format(', '.join(self._order))]

        if self._limit:
            qs += ['LIMIT {}'.format(self._limit)]

        if self._allow_filtering:
            qs += ['ALLOW FILTERING']

        return ' '.join(qs)

    #----Reads------

    def _execute_query(self):
        if self._batch:
            raise CQLEngineException(
                "Only inserts, updates, and deletes are available in batch mode")
        if self._result_cache is None:
            self._result_cache = execute(
                self._select_query(), self._where_values())
            field_names = set(
                sum([res._fields for res in self._result_cache], tuple()))
            self._construct_result = self._get_result_constructor(field_names)

    def _fill_result_cache_to_idx(self, idx):
        self._execute_query()
        if self._result_idx is None:
            self._result_idx = -1

        qty = idx - self._result_idx
        if qty < 1:
            return
        else:
            for idx in range(qty):
                self._result_idx += 1
                self._result_cache[self._result_idx] = self._construct_result(
                    self._result_cache[self._result_idx])

            # return the connection to the connection pool if we have all
            # objects
            if self._result_cache and self._result_idx == (len(self._result_cache) - 1):
                self._con = None
                self._cur = None

    def __iter__(self):
        self._execute_query()
        for idx in range(len(self._result_cache)):
            instance = self._result_cache[idx]
            # TODO: find a better way to check for this (cassandra.decoder.Row
            # is factorized :/)
            if instance.__class__.__name__ == 'Row':
                self._fill_result_cache_to_idx(idx)
            yield self._result_cache[idx]

    def __getitem__(self, s):
        self._execute_query()

        num_results = len(self._result_cache)

        if isinstance(s, slice):
            # calculate the amount of results that need to be loaded
            end = num_results if s.step is None else s.step
            if end < 0:
                end += num_results
            else:
                end -= 1
            self._fill_result_cache_to_idx(end)
            return self._result_cache[s.start:s.stop:s.step]
        else:
            # return the object at this index
            s = long(s)

            # handle negative indexing
            if s < 0:
                s += num_results

            if s >= num_results:
                raise IndexError
            else:
                self._fill_result_cache_to_idx(s)
                return self._result_cache[s]

    def _get_result_constructor(self, names):
        """
        Returns a function that will be used to instantiate query results
        """
        raise NotImplementedError

    def batch(self, batch_obj):
        """
        Adds a batch query to the mix
        :param batch_obj:
        :return:
        """
        if batch_obj is not None and not isinstance(batch_obj, BatchQuery):
            raise CQLEngineException(
                'batch_obj must be a BatchQuery instance or None')
        clone = copy.deepcopy(self)
        clone._batch = batch_obj
        return clone

    def first(self):
        try:
            return iter(self).next()
        except StopIteration:
            return None

    def all(self):
        return copy.deepcopy(self)

    def _parse_filter_arg(self, arg):
        """
        Parses a filter arg in the format:
        <colname>__<op>
        :returns: colname, op tuple
        """
        statement = arg.rsplit('__', 1)
        if len(statement) == 1:
            return arg, None
        elif len(statement) == 2:
            return statement[0], statement[1]
        else:
            raise QueryException("Can't parse '{}'".format(arg))

    def filter(self, *args, **kwargs):
        """
        Adds WHERE arguments to the queryset, returning a new queryset

        #TODO: show examples

        :rtype: AbstractQuerySet
        """
        # add arguments to the where clause filters
        clone = copy.deepcopy(self)
        for operator in args:
            if not isinstance(operator, QueryOperator):
                raise QueryException(
                    '{} is not a valid query operator'.format(operator))
            clone._where.append(operator)

        for arg, val in kwargs.items():
            col_name, col_op = self._parse_filter_arg(arg)
            # resolve column and operator
            try:
                column = self.model._get_column(col_name)
            except KeyError:
                if col_name == 'pk__token':
                    column = columns._PartitionKeysToken(self.model)
                else:
                    raise QueryException(
                        "Can't resolve column name: '{}'".format(col_name))

            # get query operator, or use equals if not supplied
            operator_class = QueryOperator.get_operator(col_op or 'EQ')
            operator = operator_class(column, val)

            clone._where.append(operator)

        return clone

    def get(self, *args, **kwargs):
        """
        Returns a single instance matching this query, optionally with additional filter kwargs.

        A DoesNotExistError will be raised if there are no rows matching the query
        A MultipleObjectsFoundError will be raised if there is more than one row matching the queyr
        """
        if args or kwargs:
            return self.filter(*args, **kwargs).get()

        self._execute_query()
        if len(self._result_cache) == 0:
            raise self.model.DoesNotExist
        elif len(self._result_cache) > 1:
            raise self.model.MultipleObjectsReturned(
                '{} objects found'.format(len(self._result_cache)))
        else:
            return self[0]

    def _get_ordering_condition(self, colname):
        order_type = 'DESC' if colname.startswith('-') else 'ASC'
        colname = colname.replace('-', '')

        return colname, order_type

    def order_by(self, *colnames):
        """
        orders the result set.
        ordering can only use clustering columns.

        Default order is ascending, prepend a '-' to the column name for descending
        """
        if len(colnames) == 0:
            clone = copy.deepcopy(self)
            clone._order = []
            return clone

        conditions = []
        for colname in colnames:
            conditions.append(
                '"{}" {}'.format(*self._get_ordering_condition(colname)))

        clone = copy.deepcopy(self)
        clone._order.extend(conditions)
        return clone

    def count(self):
        """ Returns the number of rows matched by this query """
        if self._batch:
            raise CQLEngineException(
                "Only inserts, updates, and deletes are available in batch mode")
        # TODO: check for previous query execution and return row count if it
        # exists
        if self._result_cache is None:
            qs = ['SELECT COUNT(*)']
            qs += ['FROM {}'.format(self.column_family_name)]
            if self._where:
                qs += ['WHERE {}'.format(self._where_clause())]
            if self._allow_filtering:
                qs += ['ALLOW FILTERING']

            qs = ' '.join(qs)

            result = execute(qs, self._where_values())
            return result[0][0]
        else:
            return len(self._result_cache)

    def limit(self, v):
        """
        Sets the limit on the number of results returned
        CQL has a default limit of 10,000
        """
        if not (v is None or isinstance(v, (int, long))):
            raise TypeError
        if v == self._limit:
            return self

        if v < 0:
            raise QueryException("Negative limit is not allowed")

        clone = copy.deepcopy(self)
        clone._limit = v
        return clone

    def allow_filtering(self):
        """
        Enables the unwise practive of querying on a clustering
        key without also defining a partition key
        """
        clone = copy.deepcopy(self)
        clone._allow_filtering = True
        return clone

    def _only_or_defer(self, action, fields):
        clone = copy.deepcopy(self)
        if clone._defer_fields or clone._only_fields:
            raise QueryException(
                "QuerySet alread has only or defer fields defined")

        # check for strange fields
        missing_fields = [
            f for f in fields if f not in self.model._columns.keys()]
        if missing_fields:
            raise QueryException(
                "Can't resolve fields {} in {}".format(
                    ', '.join(missing_fields), self.model.__name__))

        if action == 'defer':
            clone._defer_fields = fields
        elif action == 'only':
            clone._only_fields = fields
        else:
            raise ValueError

        return clone

    def only(self, fields):
        """ Load only these fields for the returned query """
        return self._only_or_defer('only', fields)

    def defer(self, fields):
        """ Don't load these fields for the returned query """
        return self._only_or_defer('defer', fields)

    def create(self, **kwargs):
        return self.model(**kwargs).batch(self._batch).save()

    #----delete---
    def delete(self, columns=[]):
        """
        Deletes the contents of a query
        """
        # validate where clause
        partition_key = self.model._primary_keys.values()[0]
        if not any([c.column.db_field_name == partition_key.db_field_name for c in self._where]):
            raise QueryException(
                "The partition key must be defined on delete queries")
        qs = ['DELETE FROM {}'.format(self.column_family_name)]
        qs += ['WHERE {}'.format(self._where_clause())]
        qs = ' '.join(qs)

        if self._batch:
            self._batch.add_query(qs, self._where_values())
        else:
            execute(qs, self._where_values())

    def __eq__(self, q):
        return set(self._where) == set(q._where)

    def __ne__(self, q):
        return not (self != q)


class ResultObject(dict):

    """
    adds attribute access to a dictionary
    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError


class SimpleQuerySet(AbstractQuerySet):

    """

    """

    def _get_select_statement(self):
        """ Returns the fields to be returned by the select query """
        return 'SELECT *'

    def _get_result_constructor(self, names):
        """
        Returns a function that will be used to instantiate query results
        """
        def _construct_instance(values):
            return ResultObject([(name, getattr(values, name)) for name in names])
        return _construct_instance


class ModelQuerySet(AbstractQuerySet):

    """

    """

    def _validate_where_syntax(self):
        """ Checks that a filterset will not create invalid cql """

        # check that there's either a = or IN relationship with a primary key
        # or indexed field
        equal_ops = [w for w in self._where if isinstance(w, EqualsOperator)]
        token_ops = [w for w in self._where if isinstance(w.value, Token)]
        if not any([w.column.primary_key or w.column.index for w in equal_ops]) and not token_ops:
            raise QueryException(
                'Where clauses require either a "=" or "IN" comparison with either a primary key or indexed field')

        if not self._allow_filtering:
            # if the query is not on an indexed field
            if not any([w.column.index for w in equal_ops]):
                if not any([w.column.partition_key for w in equal_ops]) and not token_ops:
                    raise QueryException(
                        'Filtering on a clustering key without a partition key is not allowed unless allow_filtering() is called on the querset')
            if any(not w.column.partition_key for w in token_ops):
                raise QueryException(
                    'The token() function is only supported on the partition key')

                # TODO: abuse this to see if we can get cql to raise an
                # exception
    def _where_clause(self):
        """ Returns a where clause based on the given filter args """
        self._validate_where_syntax()
        return super(ModelQuerySet, self)._where_clause()

    def _get_select_statement(self):
        """ Returns the fields to be returned by the select query """
        fields = self.model._columns.keys()
        if self._defer_fields:
            fields = [f for f in fields if f not in self._defer_fields]
        elif self._only_fields:
            fields = self._only_fields
        db_fields = [self.model._columns[f].db_field_name for f in fields]
        return 'SELECT {}'.format(', '.join(['"{}"'.format(f) for f in db_fields]))

    def _get_instance_constructor(self, names):
        """ returns a function used to construct model instances """
        model = self.model
        db_map = model._db_map

        def _construct_instance(values):
            field_dict = dict(
                (db_map.get(field, field), getattr(values, field)) for field in names)
            instance = model(**field_dict)
            instance._is_persisted = True
            return instance
        return _construct_instance

    def _get_result_constructor(self, names):
        """ Returns a function that will be used to instantiate query results """
        if not self._values_list:
            return self._get_instance_constructor(names)
        else:
            columns = [self.model._columns[n] for n in names]
            if self._flat_values_list:
                return lambda values: columns[0].to_python(values[0])
            else:
                return lambda values: map(lambda (c, v): c.to_python(v), zip(columns, values))

    def _get_ordering_condition(self, colname):
        colname, order_type = super(
            ModelQuerySet, self)._get_ordering_condition(colname)

        column = self.model._columns.get(colname)
        if column is None:
            raise QueryException(
                "Can't resolve the column name: '{}'".format(colname))

        # validate the column selection
        if not column.primary_key:
            raise QueryException(
                "Can't order on '{}', can only order on (clustered) primary keys".format(colname))

        pks = [v for k, v in self.model._columns.items() if v.primary_key]
        if column == pks[0]:
            raise QueryException(
                "Can't order by the first primary key (partition key), clustering (secondary) keys only")

        return column.db_field_name, order_type

    def values_list(self, *fields, **kwargs):
        """ Instructs the query set to return tuples, not model instance """
        flat = kwargs.pop('flat', False)
        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s'
                            % (kwargs.keys(),))
        if flat and len(fields) > 1:
            raise TypeError(
                "'flat' is not valid when values_list is called with more than one field.")
        clone = self.only(fields)
        clone._values_list = True
        clone._flat_values_list = flat
        return clone

    def get_model_columns(self):
        return self.model._columns

    def get_parametrized_insert_cql_query(self):
        column_names = [
            col.db_field_name for col in self.get_model_columns().values()]
        query_def = dict(
            column_family=self.model.column_family_name(),
            column_def=', '.join(column_names),
            param_def=', '.join('?' * len(column_names))
        )
        return "INSERT INTO %(column_family)s (%(column_def)s) VALUES (%(param_def)s)" % query_def

    def get_insert_parameters(self, model_instance):
        dbvalues = []
        for name in self.get_model_columns().keys():
            dbvalues.append(getattr(model_instance, name))
        return dbvalues

    def batch_insert(self, instances, batch_size, atomic=True):
        if self._batch:
            raise CQLEngineException(
                'you cant mix BatchQuery and batch inserts together')

        connection_pool = get_connection_pool()
        insert_queries_count = len(instances)
        query_per_batch = min(batch_size, insert_queries_count)

        insert_query = self.get_parametrized_insert_cql_query()

        if atomic:
            batch_query = """
                BEGIN BATCH
                {}
                APPLY BATCH;
            """
        else:
            batch_query = """
                BEGIN UNLOGGED BATCH
                {}
                APPLY BATCH;
            """

        prepared_query = connection_pool.prepare(
            batch_query.format(insert_query * query_per_batch)
        )

        results = []
        insert_chunks = chunks(instances, query_per_batch)
        for insert_chunk in insert_chunks:
            params = sum([self.get_insert_parameters(m)
                         for m in insert_chunk], [])
            if len(insert_chunk) == query_per_batch:
                results.append(
                    connection_pool.execute_async(prepared_query.bind(params)))
            elif len(insert_chunk) > 0:
                cleanup_prepared_query = connection_pool.prepare(
                    batch_query.format(insert_query * len(insert_chunk))
                )
                results.append(
                    connection_pool.execute_async(cleanup_prepared_query.bind(params)))

        # block until results are returned
        for r in results:
            r.result()


class DMLQuery(object):

    """
    A query object used for queries performing inserts, updates, or deletes

    this is usually instantiated by the model instance to be modified

    unlike the read query object, this is mutable
    """

    def __init__(self, model, instance=None, batch=None):
        self.model = model
        self.column_family_name = self.model.column_family_name()
        self.instance = instance
        self._batch = batch
        pass

    def batch(self, batch_obj):
        if batch_obj is not None and not isinstance(batch_obj, BatchQuery):
            raise CQLEngineException(
                'batch_obj must be a BatchQuery instance or None')
        self._batch = batch_obj
        return self

    def save(self):
        """
        Creates / updates a row.
        This is a blind insert call.
        All validation and cleaning needs to happen
        prior to calling this.
        """
        if self.instance is None:
            raise CQLEngineException("DML Query intance attribute is None")
        assert type(self.instance) == self.model

        # organize data
        value_pairs = []
        values = self.instance._as_dict()

        # get defined fields and their column names
        for name, col in self.model._columns.items():
            val = values.get(name)
            if val is None:
                continue
            value_pairs += [(col.db_field_name, val)]

        # construct query string
        field_names = zip(*value_pairs)[0]
        field_ids = {n: uuid4().hex for n in field_names}
        field_values = dict(value_pairs)
        query_values = {field_ids[n]: field_values[n] for n in field_names}

        qs = []
        if self.instance._has_counter or self.instance._can_update():
            qs += ["UPDATE {}".format(self.column_family_name)]
            qs += ["SET"]

            set_statements = []
            # get defined fields and their column names
            for name, col in self.model._columns.items():
                if not col.is_primary_key:
                    val = values.get(name)
                    if val is None:
                        continue
                    if isinstance(col, (BaseContainerColumn, Counter)):
                        # remove value from query values, the column will
                        # handle it
                        query_values.pop(field_ids.get(name), None)

                        val_mgr = self.instance._values[name]
                        set_statements += col.get_update_statement(
                            val, val_mgr.previous_value, query_values)

                    else:
                        set_statements += [
                            '"{}" = %({})s'.format(col.db_field_name, field_ids[col.db_field_name])]
            qs += [', '.join(set_statements)]

            qs += ['WHERE']

            where_statements = []
            for name, col in self.model._primary_keys.items():
                where_statements += ['"{}" = %({})s'.format(col.db_field_name,
                                                            field_ids[col.db_field_name])]

            qs += [' AND '.join(where_statements)]

            # clear the qs if there are no set statements and this is not a
            # counter model
            if not set_statements and not self.instance._has_counter:
                qs = []

        else:
            qs += ["INSERT INTO {}".format(self.column_family_name)]
            qs += ["({})".format(', '.join(['"{}"'.format(f)
                                            for f in field_names]))]
            qs += ['VALUES']
            qs += ["({})".format(', '.join(['%(' + field_ids[f] + ')s' for f in field_names]))]

        qs = ' '.join(qs)

        # skip query execution if it's empty
        # caused by pointless update queries
        if qs:
            if self._batch:
                self._batch.add_query(qs, query_values)
            else:
                execute(qs, query_values)

        # delete nulled columns and removed map keys
        qs = ['DELETE']
        query_values = {}

        del_statements = []
        for k, v in self.instance._values.items():
            col = v.column
            if v.deleted:
                del_statements += ['"{}"'.format(col.db_field_name)]
            elif isinstance(col, Map):
                del_statements += col.get_delete_statement(
                    v.value, v.previous_value, query_values)

        if del_statements:
            qs += [', '.join(del_statements)]

            qs += ['FROM {}'.format(self.column_family_name)]

            qs += ['WHERE']
            where_statements = []
            for name, col in self.model._primary_keys.items():
                field_id = uuid4().hex
                query_values[field_id] = field_values[name]
                where_statements += [
                    '"{}" = %({})s'.format(col.db_field_name, field_id)]
            qs += [' AND '.join(where_statements)]

            qs = ' '.join(qs)

            if self._batch:
                self._batch.add_query(qs, query_values)
            else:
                execute(qs, query_values)

    def delete(self):
        """ Deletes one instance """
        if self.instance is None:
            raise CQLEngineException("DML Query intance attribute is None")
        field_values = {}
        qs = ['DELETE FROM {}'.format(self.column_family_name)]
        qs += ['WHERE']
        where_statements = []
        for name, col in self.model._primary_keys.items():
            field_id = uuid4().hex
            field_values[field_id] = getattr(self.instance, name)
            where_statements += ['"{}" = %({})s'.format(col.db_field_name,
                                                        field_id)]

        qs += [' AND '.join(where_statements)]
        qs = ' '.join(qs)

        if self._batch:
            self._batch.add_query(qs, field_values)
        else:
            execute(qs, field_values)
