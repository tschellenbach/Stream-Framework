from collections import OrderedDict
import re

from cqlengine import columns
from cqlengine.exceptions import ModelException, CQLEngineException, ValidationError
from cqlengine.query import ModelQuerySet, DMLQuery, AbstractQueryableColumn
from cqlengine.query import DoesNotExist as _DoesNotExist
from cqlengine.query import MultipleObjectsReturned as _MultipleObjectsReturned


class ModelDefinitionException(ModelException):
    pass

DEFAULT_KEYSPACE = 'cqlengine'


class hybrid_classmethod(object):

    """
    Allows a method to behave as both a class method and
    normal instance method depending on how it's called
    """

    def __init__(self, clsmethod, instmethod):
        self.clsmethod = clsmethod
        self.instmethod = instmethod

    def __get__(self, instance, owner):
        if instance is None:
            return self.clsmethod.__get__(owner, owner)
        else:
            return self.instmethod.__get__(instance, owner)

    def __call__(self, *args, **kwargs):
        """
        Just a hint to IDEs that it's ok to call this
        """
        raise NotImplementedError


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
        return model.__queryset__(model)

    def __call__(self, *args, **kwargs):
        """
        Just a hint to IDEs that it's ok to call this

        :rtype: ModelQuerySet
        """
        raise NotImplementedError


class ColumnQueryEvaluator(AbstractQueryableColumn):

    """
    Wraps a column and allows it to be used in comparator
    expressions, returning query operators

    ie:
    Model.column == 5
    """

    def __init__(self, column):
        self.column = column

    def _get_column(self):
        return self.column


class ColumnDescriptor(object):

    """
    Handles the reading and writing of column values to and from
    a model instance's value manager, as well as creating
    comparator queries
    """

    def __init__(self, column):
        """
        :param column:
        :type column: columns.Column
        :return:
        """
        self.column = column
        self.query_evaluator = ColumnQueryEvaluator(self.column)

    def __get__(self, instance, owner):
        """
        Returns either the value or column, depending
        on if an instance is provided or not

        :param instance: the model instance
        :type instance: Model
        """

        if instance:
            return instance._values[self.column.column_name].getval()
        else:
            return self.query_evaluator

    def __set__(self, instance, value):
        """
        Sets the value on an instance, raises an exception with classes
        TODO: use None instance to create update statements
        """
        if instance:
            return instance._values[self.column.column_name].setval(value)
        else:
            raise AttributeError('cannot reassign column values')

    def __delete__(self, instance):
        """
        Sets the column value to None, if possible
        """
        if instance:
            if self.column.can_delete:
                instance._values[self.column.column_name].delval()
            else:
                raise AttributeError(
                    'cannot delete {} columns'.format(self.column.column_name))


class BaseModel(object):

    """
    The base model class, don't inherit from this, inherit from Model, defined below
    """

    class DoesNotExist(_DoesNotExist):
        pass

    class MultipleObjectsReturned(_MultipleObjectsReturned):
        pass

    objects = QuerySetDescriptor()

    # table names will be generated automatically from it's model and package name
    # however, you can also define them manually here
    __table_name__ = None

    # the keyspace for this model
    __keyspace__ = None

    # compaction options
    __compaction__ = None
    __compaction_tombstone_compaction_interval__ = None
    __compaction_tombstone_threshold = None

    # compaction - size tiered options
    __compaction_bucket_high__ = None
    __compaction_bucket_low__ = None
    __compaction_max_threshold__ = None
    __compaction_min_threshold__ = None
    __compaction_min_sstable_size__ = None

    # compaction - leveled options
    __compaction_sstable_size_in_mb__ = None

    # end compaction
    # the queryset class used for this class
    __queryset__ = ModelQuerySet
    __dmlquery__ = DMLQuery

    __read_repair_chance__ = 0.1

    def __init__(self, **values):
        self._values = {}

        extra_columns = set(values.keys()) - set(self._columns.keys())
        if extra_columns:
            raise ValidationError(
                "Incorrect columns passed: {}".format(extra_columns))

        for name, column in self._columns.items():
            value = values.get(name, None)
            if value is not None or isinstance(column, columns.BaseContainerColumn):
                value = column.to_python(value)
            value_mngr = column.value_manager(self, column, value)
            self._values[name] = value_mngr

        # a flag set by the deserializer to indicate
        # that update should be used when persisting changes
        self._is_persisted = False
        self._batch = None

    def _can_update(self):
        """
        Called by the save function to check if this should be
        persisted with update or insert

        :return:
        """
        if not self._is_persisted:
            return False
        pks = self._primary_keys.keys()
        return all([not self._values[k].changed for k in self._primary_keys])

    @classmethod
    def _get_keyspace(cls):
        """ Returns the manual keyspace, if set, otherwise the default keyspace """
        return cls.__keyspace__ or DEFAULT_KEYSPACE

    @classmethod
    def _get_column(cls, name):
        """
        Returns the column matching the given name, raising a key error if
        it doesn't exist

        :param name: the name of the column to return
        :rtype: Column
        """
        return cls._columns[name]

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        # check attribute keys
        keys = set(self._columns.keys())
        other_keys = set(self._columns.keys())
        if keys != other_keys:
            return False

        # check that all of the attributes match
        for key in other_keys:
            if getattr(self, key, None) != getattr(other, key, None):
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def column_family_name(cls, include_keyspace=True):
        """
        Returns the column family name if it's been defined
        otherwise, it creates it from the module and class name
        """
        cf_name = ''
        if cls.__table_name__:
            cf_name = cls.__table_name__.lower()
        else:
            camelcase = re.compile(r'([a-z])([A-Z])')
            ccase = lambda s: camelcase.sub(
                lambda v: '{}_{}'.format(v.group(1), v.group(2).lower()), s)

            cf_name += ccase(cls.__name__)
            # trim to less than 48 characters or cassandra will complain
            cf_name = cf_name[-48:]
            cf_name = cf_name.lower()
            cf_name = re.sub(r'^_+', '', cf_name)
        if not include_keyspace:
            return cf_name
        return '{}.{}'.format(cls._get_keyspace(), cf_name)

    def validate(self):
        """ Cleans and validates the field values """
        for name, col in self._columns.items():
            val = col.validate(getattr(self, name))
            setattr(self, name, val)

    def _as_dict(self):
        """ Returns a map of column names to cleaned values """
        values = self._dynamic_columns or {}
        for name, col in self._columns.items():
            values[name] = getattr(self, name, None)
        print values
        return values

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def all(cls):
        return cls.objects.all()

    @classmethod
    def filter(cls, *args, **kwargs):
        return cls.objects.filter(*args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.get(*args, **kwargs)

    def save(self):
        is_new = self.pk is None
        self.validate()
        self.__dmlquery__(self.__class__, self, batch=self._batch).save()

        # reset the value managers
        for v in self._values.values():
            v.reset_previous_value()
        self._is_persisted = True

        return self

    def delete(self):
        """ Deletes this instance """
        self.__dmlquery__(self.__class__, self, batch=self._batch).delete()

    @classmethod
    def _class_batch(cls, batch):
        return cls.objects.batch(batch)

    def _inst_batch(self, batch):
        self._batch = batch
        return self

    batch = hybrid_classmethod(_class_batch, _inst_batch)


class ModelMetaClass(type):

    def __new__(cls, name, bases, attrs):
        """
        """
        # move column definitions into columns dict
        # and set default column names
        column_dict = OrderedDict()
        primary_keys = OrderedDict()
        pk_name = None

        # get inherited properties
        inherited_columns = OrderedDict()
        for base in bases:
            for k, v in getattr(base, '_defined_columns', {}).items():
                inherited_columns.setdefault(k, v)

        # short circuit __abstract__ inheritance
        is_abstract = attrs['__abstract__'] = attrs.get('__abstract__', False)

        def _transform_column(col_name, col_obj):
            column_dict[col_name] = col_obj
            if col_obj.primary_key:
                primary_keys[col_name] = col_obj
            col_obj.set_column_name(col_name)
            # set properties
            attrs[col_name] = ColumnDescriptor(col_obj)

        column_definitions = [
            (k, v) for k, v in attrs.items() if isinstance(v, columns.Column)]
        column_definitions = sorted(
            column_definitions, lambda x, y: cmp(x[1].position, y[1].position))

        column_definitions = inherited_columns.items() + column_definitions

        defined_columns = OrderedDict(column_definitions)

        # prepend primary key if one hasn't been defined
        if not is_abstract and not any([v.primary_key for k, v in column_definitions]):
            raise ModelDefinitionException(
                "At least 1 primary key is required.")

        counter_columns = [
            c for c in defined_columns.values() if isinstance(c, columns.Counter)]
        data_columns = [c for c in defined_columns.values(
        ) if not c.primary_key and not isinstance(c, columns.Counter)]
        if counter_columns and data_columns:
            raise ModelDefinitionException(
                'counter models may not have data columns')

        has_partition_keys = any(
            v.partition_key for (k, v) in column_definitions)

        # TODO: check that the defined columns don't conflict with any of the Model API's existing attributes/methods
        # transform column definitions
        for k, v in column_definitions:
            # counter column primary keys are not allowed
            if (v.primary_key or v.partition_key) and isinstance(v, (columns.Counter, columns.BaseContainerColumn)):
                raise ModelDefinitionException(
                    'counter columns and container columns cannot be used as primary keys')

            # this will mark the first primary key column as a partition
            # key, if one hasn't been set already
            if not has_partition_keys and v.primary_key:
                v.partition_key = True
                has_partition_keys = True
            _transform_column(k, v)

        partition_keys = OrderedDict(
            k for k in primary_keys.items() if k[1].partition_key)
        clustering_keys = OrderedDict(
            k for k in primary_keys.items() if not k[1].partition_key)

        # setup partition key shortcut
        if len(partition_keys) == 0:
            if not is_abstract:
                raise ModelException(
                    "at least one partition key must be defined")
        if len(partition_keys) == 1:
            pk_name = partition_keys.keys()[0]
            attrs['pk'] = attrs[pk_name]
        else:
            # composite partition key case, get/set a tuple of values
            _get = lambda self: tuple(
                self._values[c].getval() for c in partition_keys.keys())
            _set = lambda self, val: tuple(
                self._values[c].setval(v) for (c, v) in zip(partition_keys.keys(), val))
            attrs['pk'] = property(_get, _set)

        # some validation
        col_names = set()
        for v in column_dict.values():
            # check for duplicate column names
            if v.db_field_name in col_names:
                raise ModelException(
                    "{} defines the column {} more than once".format(name, v.db_field_name))
            if v.clustering_order and not (v.primary_key and not v.partition_key):
                raise ModelException(
                    "clustering_order may be specified only for clustering primary keys")
            if v.clustering_order and v.clustering_order.lower() not in ('asc', 'desc'):
                raise ModelException("invalid clustering order {} for column {}".format(
                    repr(v.clustering_order), v.db_field_name))
            col_names.add(v.db_field_name)

        # create db_name -> model name map for loading
        db_map = {}
        for field_name, col in column_dict.items():
            db_map[col.db_field_name] = field_name

        # add management members to the class
        attrs['_columns'] = column_dict
        attrs['_primary_keys'] = primary_keys
        attrs['_defined_columns'] = defined_columns
        attrs['_db_map'] = db_map
        attrs['_pk_name'] = pk_name
        attrs['_dynamic_columns'] = {}

        attrs['_partition_keys'] = partition_keys
        attrs['_clustering_keys'] = clustering_keys
        attrs['_has_counter'] = len(counter_columns) > 0

        # setup class exceptions
        DoesNotExistBase = None
        for base in bases:
            DoesNotExistBase = getattr(base, 'DoesNotExist', None)
            if DoesNotExistBase is not None:
                break
        DoesNotExistBase = DoesNotExistBase or attrs.pop(
            'DoesNotExist', BaseModel.DoesNotExist)
        attrs['DoesNotExist'] = type('DoesNotExist', (DoesNotExistBase,), {})

        MultipleObjectsReturnedBase = None
        for base in bases:
            MultipleObjectsReturnedBase = getattr(
                base, 'MultipleObjectsReturned', None)
            if MultipleObjectsReturnedBase is not None:
                break
        MultipleObjectsReturnedBase = DoesNotExistBase or attrs.pop(
            'MultipleObjectsReturned', BaseModel.MultipleObjectsReturned)
        attrs['MultipleObjectsReturned'] = type(
            'MultipleObjectsReturned', (MultipleObjectsReturnedBase,), {})

        # create the class and add a QuerySet to it
        klass = super(ModelMetaClass, cls).__new__(cls, name, bases, attrs)
        return klass


class Model(BaseModel):

    """
    the db name for the column family can be set as the attribute db_name, or
    it will be genertaed from the class name
    """
    __abstract__ = True
    __metaclass__ = ModelMetaClass
