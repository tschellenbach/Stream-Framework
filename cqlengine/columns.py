from cassandra import cqltypes
from copy import copy
from datetime import datetime
from datetime import date
import re
from uuid import uuid1, uuid4

from cqlengine.exceptions import ValidationError


def __escape_quotes(term):
    assert isinstance(term, basestring)
    return term.replace("'", "''")


def cql_quote(term, cql_major_version=3):
    if isinstance(term, unicode):
        return "'%s'" % __escape_quotes(term.encode('utf8'))
    elif isinstance(term, str):
        return "'%s'" % __escape_quotes(str(term))
    elif isinstance(term, bool) and cql_major_version == 2:
        return "'%s'" % str(term)
    else:
        return str(term)


internal_clq_type_mapping = {
    'text': cqltypes.UTF8Type,
    'blob': cqltypes.BytesType,
    'ascii': cqltypes.AsciiType,
    'text': cqltypes.UTF8Type,
    'int': cqltypes.Int32Type,
    'varint': cqltypes.IntegerType,
    'timestamp': cqltypes.DateType,
    'uuid': cqltypes.UUIDType,
    'timeuuid': cqltypes.TimeUUIDType,
    'boolean': cqltypes.BooleanType,
    'double': cqltypes.DoubleType,
}


class BaseValueManager(object):

    def __init__(self, instance, column, value):
        self.instance = instance
        self.column = column
        self.previous_value = copy(value)
        self.value = value

    @property
    def deleted(self):
        return self.value is None and self.previous_value is not None

    @property
    def changed(self):
        """
        Indicates whether or not this value has changed.

        :rtype: boolean

        """
        return self.value != self.previous_value

    def reset_previous_value(self):
        self.previous_value = copy(self.value)

    def getval(self):
        return self.value

    def setval(self, val):
        self.value = val

    def delval(self):
        self.value = None

    def get_property(self):
        _get = lambda slf: self.getval()
        _set = lambda slf, val: self.setval(val)
        _del = lambda slf: self.delval()

        if self.column.can_delete:
            return property(_get, _set, _del)
        else:
            return property(_get, _set)


class ValueQuoter(object):

    """
    contains a single value, which will quote itself for CQL insertion statements
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False


class Column(object):

    # the cassandra type this column maps to
    db_type = None

    value_manager = BaseValueManager

    instance_counter = 0

    def __init__(self,
                 primary_key=False,
                 partition_key=False,
                 index=False,
                 db_field=None,
                 default=None,
                 required=False,
                 clustering_order=None):
        """
        :param primary_key: bool flag, indicates this column is a primary key. The first primary key defined
            on a model is the partition key (unless partition keys are set), all others are cluster keys
        :param partition_key: indicates that this column should be the partition key, defining
            more than one partition key column creates a compound partition key
        :param index: bool flag, indicates an index should be created for this column
        :param db_field: the fieldname this field will map to in the database
        :param default: the default value, can be a value or a callable (no args)
        :param required: boolean, is the field required? Model validation will raise and
            exception if required is set to True and there is a None value assigned
        :param clustering_order: only applicable on clustering keys (primary keys that are not partition keys)
            determines the order that the clustering keys are sorted on disk
        """
        self.partition_key = partition_key
        self.primary_key = partition_key or primary_key
        self.index = index
        self.db_field = db_field
        self.default = default
        self.required = required
        self.clustering_order = clustering_order
        # the column name in the model definition
        self.column_name = None

        self.value = None

        # keep track of instantiation order
        self.position = Column.instance_counter
        Column.instance_counter += 1

    def validate(self, value):
        '''
        add extra validation (before cassandra-driver)
        '''
        if value is None:
            if self.has_default:
                value = self.get_default()
            elif self.required:
                value = self.ctype.validate(value)
        return value

    def to_python(self, value):
        '''
        does some extra python-python conversion
        eg. convert a datetime to date for a date column
        '''
        return value

    @property
    def ctype(self):
        '''
        the cassandra type identifier as defined in 
        python cassandra driver
        '''
        return internal_clq_type_mapping[self.db_type]

    @property
    def has_default(self):
        return self.default is not None

    @property
    def is_primary_key(self):
        return self.primary_key

    @property
    def can_delete(self):
        return not self.primary_key

    def get_default(self):
        if self.has_default:
            if callable(self.default):
                return self.default()
            else:
                return self.default

    def get_column_def(self):
        """
        Returns a column definition for CQL table definition
        """
        return '{} {}'.format(self.cql, self.db_type)

    def set_column_name(self, name):
        """
        Sets the column name during document class construction
        This value will be ignored if db_field is set in __init__
        """
        self.column_name = name

    @property
    def db_field_name(self):
        """ Returns the name of the cql name of this column """
        return self.db_field or self.column_name

    @property
    def db_index_name(self):
        """ Returns the name of the cql index """
        return 'index_{}'.format(self.db_field_name)

    @property
    def cql(self):
        return self.get_cql()

    def get_cql(self):
        return '"{}"'.format(self.db_field_name)


class Bytes(Column):
    db_type = 'blob'


class Ascii(Column):
    db_type = 'ascii'


class Text(Column):
    db_type = 'text'

    def __init__(self, *args, **kwargs):
        self.min_length = kwargs.pop(
            'min_length', 1 if kwargs.get('required', False) else None)
        self.max_length = kwargs.pop('max_length', None)
        super(Text, self).__init__(*args, **kwargs)

    def validate(self, value):
        value = super(Text, self).validate(value)
        if value is None:
            return
        if not isinstance(value, (basestring, bytearray)) and value is not None:
            raise ValidationError('{} is not a string'.format(type(value)))
        if self.max_length:
            if len(value) > self.max_length:
                raise ValidationError(
                    '{} is longer than {} characters'.format(self.column_name, self.max_length))
        if self.min_length:
            if len(value) < self.min_length:
                raise ValidationError(
                    '{} is shorter than {} characters'.format(self.column_name, self.min_length))
        return value


class Integer(Column):
    db_type = 'int'


class VarInt(Column):
    db_type = 'varint'


class CounterValueManager(BaseValueManager):

    def __init__(self, instance, column, value):
        super(CounterValueManager, self).__init__(instance, column, value)
        self.value = self.value or 0
        self.previous_value = self.previous_value or 0


class Counter(Integer):
    db_type = 'counter'

    value_manager = CounterValueManager

    def __init__(self,
                 index=False,
                 db_field=None,
                 required=False):
        super(Counter, self).__init__(
            primary_key=False,
            partition_key=False,
            index=index,
            db_field=db_field,
            default=0,
            required=required,
        )

    def get_update_statement(self, val, prev, ctx):
        prev = prev or 0
        field_id = uuid4().hex

        delta = val - prev
        sign = '-' if delta < 0 else '+'
        delta = abs(delta)
        ctx[field_id] = delta
        return ['"{0}" = "{0}" {1} {2}'.format(self.db_field_name, sign, delta)]


class DateTime(Column):
    db_type = 'timestamp'


class Date(Column):
    db_type = 'timestamp'

    def to_python(self, value):
        value = super(Date, self).to_python(value)
        if isinstance(value, datetime):
            return value.date()
        return value


class UUID(Column):

    """
    Type 1 or 4 UUID
    """
    db_type = 'uuid'

    re_uuid = re.compile(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

    def validate(self, value):
        val = super(UUID, self).validate(value)
        if val is None:
            return
        from uuid import UUID as _UUID
        if isinstance(val, _UUID):
            return val
        if isinstance(val, basestring) and self.re_uuid.match(val):
            return _UUID(val)
        raise ValidationError("{} is not a valid uuid".format(value))


from uuid import UUID as pyUUID, getnode


class TimeUUID(UUID):

    """
    UUID containing timestamp
    """

    db_type = 'timeuuid'

    @classmethod
    def from_datetime(self, dt):
        """
        generates a UUID for a given datetime

        :param dt: datetime
        :type dt: datetime
        :return:
        """
        global _last_timestamp

        epoch = datetime(1970, 1, 1, tzinfo=dt.tzinfo)

        offset = 0
        if epoch.tzinfo:
            offset_delta = epoch.tzinfo.utcoffset(epoch)
            offset = offset_delta.days * 24 * 3600 + offset_delta.seconds

        timestamp = (dt - epoch).total_seconds() - offset

        node = None
        clock_seq = None

        nanoseconds = int(timestamp * 1e9)
        timestamp = int(nanoseconds // 100) + 0x01b21dd213814000L

        if clock_seq is None:
            import random
            clock_seq = random.randrange(1 << 14L)  # instead of stable storage
        time_low = timestamp & 0xffffffffL
        time_mid = (timestamp >> 32L) & 0xffffL
        time_hi_version = (timestamp >> 48L) & 0x0fffL
        clock_seq_low = clock_seq & 0xffL
        clock_seq_hi_variant = (clock_seq >> 8L) & 0x3fL
        if node is None:
            node = getnode()
        return pyUUID(fields=(time_low, time_mid, time_hi_version,
                              clock_seq_hi_variant, clock_seq_low, node), version=1)


class Boolean(Column):
    db_type = 'boolean'


class Float(Column):
    db_type = 'double'

    def validate(self, value):
        value = super(Float, self).validate(value)
        if value is None:
            return
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError("{} is not a valid float".format(value))


class Decimal(Column):
    db_type = 'decimal'


class BaseContainerColumn(Column):

    """
    Base Container type
    """

    def __init__(self, value_type, **kwargs):
        """
        :param value_type: a column class indicating the types of the value
        """
        inheritance_comparator = issubclass if isinstance(
            value_type, type) else isinstance
        if not inheritance_comparator(value_type, Column):
            raise ValidationError('value_type must be a column class')
        if inheritance_comparator(value_type, BaseContainerColumn):
            raise ValidationError('container types cannot be nested')
        if value_type.db_type is None:
            raise ValidationError(
                'value_type cannot be an abstract column type')

        if isinstance(value_type, type):
            self.value_type = value_type
            self.value_col = self.value_type()
        else:
            self.value_col = value_type
            self.value_type = self.value_col.__class__

        super(BaseContainerColumn, self).__init__(**kwargs)

    def get_column_def(self):
        """
        Returns a column definition for CQL table definition
        """
        db_type = self.db_type.format(self.value_type.db_type)
        return '{} {}'.format(self.db_field_name, db_type)

    def get_update_statement(self, val, prev, ctx):
        """
        Used to add partial update statements
        """
        raise NotImplementedError


class Set(BaseContainerColumn):

    """
    Stores a set of unordered, unique values

    http://www.datastax.com/docs/1.2/cql_cli/using/collections
    """
    db_type = 'set<{}>'

    class Quoter(ValueQuoter):

        def __str__(self):
            cq = cql_quote
            return '{' + ', '.join([cq(v) for v in self.value]) + '}'

    def __init__(self, value_type, strict=True, default=set, **kwargs):
        """
        :param value_type: a column class indicating the types of the value
        :param strict: sets whether non set values will be coerced to set
            type on validation, or raise a validation error, defaults to True
        """
        self.strict = strict

        super(Set, self).__init__(value_type, default=default, **kwargs)

    def validate(self, value):
        val = super(Set, self).validate(value)
        if val is None:
            return
        types = (set,) if self.strict else (set, list, tuple)
        if not isinstance(val, types):
            if self.strict:
                raise ValidationError('{} is not a set object'.format(val))
            else:
                raise ValidationError(
                    '{} cannot be coerced to a set object'.format(val))

        return {self.value_col.validate(v) for v in val}

    def to_python(self, value):
        if value is None:
            return set()
        return {self.value_col.to_python(v) for v in value}

    def get_update_statement(self, val, prev, ctx):
        """
        Returns statements that will be added to an object's update statement
        also updates the query context

        :param val: the current column value
        :param prev: the previous column value
        :param ctx: the values that will be passed to the query
        :rtype: list
        """

        # remove from Quoter containers, if applicable
        if isinstance(val, self.Quoter):
            val = val.value
        if isinstance(prev, self.Quoter):
            prev = prev.value

        if val is None or val == prev:
            # don't return anything if the new value is the same as
            # the old one, or if the new value is none
            return []
        elif prev is None or not any({v in prev for v in val}):
            field = uuid1().hex
            ctx[field] = self.Quoter(val)
            return ['"{}" = {{}}'.format(self.db_field_name, field)]
        else:
            # partial update time
            to_create = val - prev
            to_delete = prev - val
            statements = []

            if to_create:
                field_id = uuid1().hex
                ctx[field_id] = self.Quoter(to_create)
                statements += [
                    '"{0}" = "{0}" + %({1})s'.format(self.db_field_name, field_id)]

            if to_delete:
                field_id = uuid1().hex
                ctx[field_id] = self.Quoter(to_delete)
                statements += [
                    '"{0}" = "{0}" - %({1})s'.format(self.db_field_name, field_id)]

            return statements


class List(BaseContainerColumn):

    """
    Stores a list of ordered values

    http://www.datastax.com/docs/1.2/cql_cli/using/collections_list
    """
    db_type = 'list<{}>'

    class Quoter(ValueQuoter):

        def __str__(self):
            cq = cql_quote
            return '[' + ', '.join([cq(v) for v in self.value]) + ']'

    def __init__(self, value_type, default=set, **kwargs):
        return super(List, self).__init__(value_type=value_type, default=default, **kwargs)

    def validate(self, value):
        val = super(List, self).validate(value)
        if val is None:
            return
        if not isinstance(val, (set, list, tuple)):
            raise ValidationError('{} is not a list object'.format(val))
        return [self.value_col.validate(v) for v in val]

    def to_python(self, value):
        if value is None:
            return []
        return [self.value_col.to_python(v) for v in value]

    def get_update_statement(self, val, prev, values):
        """
        Returns statements that will be added to an object's update statement
        also updates the query context
        """
        # remove from Quoter containers, if applicable
        if isinstance(val, self.Quoter):
            val = val.value
        if isinstance(prev, self.Quoter):
            prev = prev.value

        def _insert():
            field_id = uuid1().hex
            values[field_id] = self.Quoter(val)
            return ['"{}" = {}'.format(self.db_field_name, field_id)]

        if val is None or val == prev:
            return []

        elif prev is None:
            return _insert()

        elif len(val) < len(prev):
            # if elements have been removed,
            # rewrite the whole list
            return _insert()

        elif len(prev) == 0:
            # if we're updating from an empty
            # list, do a complete insert
            return _insert()

        else:
            # the prepend and append lists,
            # if both of these are still None after looking
            # at both lists, an insert statement will be returned
            prepend = None
            append = None

            # the max start idx we want to compare
            search_space = len(val) - max(0, len(prev) - 1)

            # the size of the sub lists we want to look at
            search_size = len(prev)

            for i in range(search_space):
                # slice boundary
                j = i + search_size
                sub = val[i:j]
                idx_cmp = lambda idx: prev[idx] == sub[idx]
                if idx_cmp(0) and idx_cmp(-1) and prev == sub:
                    prepend = val[:i]
                    append = val[j:]
                    break

            # create update statements
            if prepend is append is None:
                return _insert()

            statements = []
            if prepend:
                field_id = uuid1().hex
                # CQL seems to prepend element at a time, starting
                # with the element at idx 0, we can either reverse
                # it here, or have it inserted in reverse
                prepend.reverse()
                values[field_id] = self.Quoter(prepend)
                statements += [
                    '"{0}" = %({1})s + "{0}"'.format(self.db_field_name, field_id)]

            if append:
                field_id = uuid1().hex
                values[field_id] = self.Quoter(append)
                statements += [
                    '"{0}" = "{0}" + %({1})s'.format(self.db_field_name, field_id)]

            return statements


class Map(BaseContainerColumn):

    """
    Stores a key -> value map (dictionary)

    http://www.datastax.com/docs/1.2/cql_cli/using/collections_map
    """

    db_type = 'map<{}, {}>'

    class Quoter(ValueQuoter):

        def __str__(self):
            cq = cql_quote
            return '{' + ', '.join([cq(k) + ':' + cq(v) for k, v in self.value.items()]) + '}'

    def __init__(self, key_type, value_type, default=dict, **kwargs):
        """
        :param key_type: a column class indicating the types of the key
        :param value_type: a column class indicating the types of the value
        """
        inheritance_comparator = issubclass if isinstance(
            key_type, type) else isinstance
        if not inheritance_comparator(key_type, Column):
            raise ValidationError('key_type must be a column class')
        if inheritance_comparator(key_type, BaseContainerColumn):
            raise ValidationError('container types cannot be nested')
        if key_type.db_type is None:
            raise ValidationError('key_type cannot be an abstract column type')

        if isinstance(key_type, type):
            self.key_type = key_type
            self.key_col = self.key_type()
        else:
            self.key_col = key_type
            self.key_type = self.key_col.__class__
        super(Map, self).__init__(value_type, default=default, **kwargs)

    def get_column_def(self):
        """
        Returns a column definition for CQL table definition
        """
        db_type = self.db_type.format(
            self.key_type.db_type,
            self.value_type.db_type
        )
        return '{} {}'.format(self.db_field_name, db_type)

    def validate(self, value):
        val = super(Map, self).validate(value)
        if val is None:
            return
        if not isinstance(val, dict):
            raise ValidationError('{} is not a dict object'.format(val))
        return {self.key_col.validate(k): self.value_col.validate(v) for k, v in val.items()}

    def to_python(self, value):
        if value is None:
            return {}
        if value is not None:
            return {self.key_col.to_python(k): self.value_col.to_python(v) for k, v in value.items()}

    def get_update_statement(self, val, prev, ctx):
        """
        http://www.datastax.com/docs/1.2/cql_cli/using/collections_map#deletion
        """
        # remove from Quoter containers, if applicable
        if isinstance(val, self.Quoter):
            val = val.value
        if isinstance(prev, self.Quoter):
            prev = prev.value
        val = val or {}
        prev = prev or {}

        # get the updated map
        update = {k: v for k, v in val.items() if v != prev.get(k)}

        statements = []
        for k, v in update.items():
            key_id = uuid1().hex
            val_id = uuid1().hex
            ctx[key_id] = k
            ctx[val_id] = v
            statements += ['"{}"[%({})s] = %({})s'.format(self.db_field_name,
                                                          key_id, val_id)]

        return statements

    def get_delete_statement(self, val, prev, ctx):
        """
        Returns statements that will be added to an object's delete statement
        also updates the query context, used for removing keys from a map
        """
        if val is prev is None:
            return []
        if isinstance(val, self.Quoter):
            val = val.value
        if isinstance(prev, self.Quoter):
            prev = prev.value

        old_keys = set(prev.keys()) if prev else set()
        new_keys = set(val.keys()) if val else set()
        del_keys = old_keys - new_keys

        del_statements = []
        for key in del_keys:
            field_id = uuid1().hex
            ctx[field_id] = key
            del_statements += ['"{}"[%({})s]'.format(self.db_field_name,
                                                     field_id)]

        return del_statements


class _PartitionKeysToken(Column):

    """
    virtual column representing token of partition columns.
    Used by filter(pk__token=Token(...)) filters
    """

    def __init__(self, model):
        self.partition_columns = model._partition_keys.values()
        super(_PartitionKeysToken, self).__init__(partition_key=True)

    def get_cql(self):
        return "token({})".format(", ".join(c.cql for c in self.partition_columns))
