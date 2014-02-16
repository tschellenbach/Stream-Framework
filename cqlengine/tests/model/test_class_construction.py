from uuid import uuid4
from cqlengine.query import QueryException, ModelQuerySet, DMLQuery
from cqlengine.tests.base import BaseCassEngTestCase

from cqlengine.exceptions import ModelException, CQLEngineException
from cqlengine.models import Model, ModelDefinitionException, ColumnQueryEvaluator
from cqlengine import columns
import cqlengine

class TestModelClassFunction(BaseCassEngTestCase):
    """
    Tests verifying the behavior of the Model metaclass
    """

    def test_column_attributes_handled_correctly(self):
        """
        Tests that column attributes are moved to a _columns dict
        and replaced with simple value attributes
        """

        class TestModel(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            text = columns.Text()

        #check class attibutes
        self.assertHasAttr(TestModel, '_columns')
        self.assertHasAttr(TestModel, 'id')
        self.assertHasAttr(TestModel, 'text')

        #check instance attributes
        inst = TestModel()
        self.assertHasAttr(inst, 'id')
        self.assertHasAttr(inst, 'text')
        self.assertIsNone(inst.id)
        self.assertIsNone(inst.text)

    def test_db_map(self):
        """
        Tests that the db_map is properly defined
        -the db_map allows columns
        """
        class WildDBNames(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            content = columns.Text(db_field='words_and_whatnot')
            numbers = columns.Integer(db_field='integers_etc')

        db_map = WildDBNames._db_map
        self.assertEquals(db_map['words_and_whatnot'], 'content')
        self.assertEquals(db_map['integers_etc'], 'numbers')

    def test_attempting_to_make_duplicate_column_names_fails(self):
        """
        Tests that trying to create conflicting db column names will fail
        """

        with self.assertRaises(ModelException):
            class BadNames(Model):
                words = columns.Text()
                content = columns.Text(db_field='words')

    def test_column_ordering_is_preserved(self):
        """
        Tests that the _columns dics retains the ordering of the class definition
        """

        class Stuff(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            words = columns.Text()
            content = columns.Text()
            numbers = columns.Integer()

        self.assertEquals(Stuff._columns.keys(), ['id', 'words', 'content', 'numbers'])

    def test_exception_raised_when_creating_class_without_pk(self):
        with self.assertRaises(ModelDefinitionException):
            class TestModel(Model):
                count   = columns.Integer()
                text    = columns.Text(required=False)


    def test_value_managers_are_keeping_model_instances_isolated(self):
        """
        Tests that instance value managers are isolated from other instances
        """
        class Stuff(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            num = columns.Integer()

        inst1 = Stuff(num=5)
        inst2 = Stuff(num=7)

        self.assertNotEquals(inst1.num, inst2.num)
        self.assertEquals(inst1.num, 5)
        self.assertEquals(inst2.num, 7)

    def test_superclass_fields_are_inherited(self):
        """
        Tests that fields defined on the super class are inherited properly
        """
        class TestModel(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            text = columns.Text()

        class InheritedModel(TestModel):
            numbers = columns.Integer()

        assert 'text' in InheritedModel._columns
        assert 'numbers' in InheritedModel._columns

    def test_column_family_name_generation(self):
        """ Tests that auto column family name generation works as expected """
        class TestModel(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            text = columns.Text()

        assert TestModel.column_family_name(include_keyspace=False) == 'test_model'

    def test_normal_fields_can_be_defined_between_primary_keys(self):
        """
        Tests tha non primary key fields can be defined between primary key fields
        """

    def test_at_least_one_non_primary_key_column_is_required(self):
        """
        Tests that an error is raised if a model doesn't contain at least one primary key field
        """

    def test_model_keyspace_attribute_must_be_a_string(self):
        """
        Tests that users can't set the keyspace to None, or something else
        """

    def test_indexes_arent_allowed_on_models_with_multiple_primary_keys(self):
        """
        Tests that attempting to define an index on a model with multiple primary keys fails
        """

    def test_meta_data_is_not_inherited(self):
        """
        Test that metadata defined in one class, is not inherited by subclasses
        """

    def test_partition_keys(self):
        """
        Test compound partition key definition
        """
        class ModelWithPartitionKeys(cqlengine.Model):
            id = columns.UUID(primary_key=True, default=lambda:uuid4())
            c1 = cqlengine.Text(primary_key=True)
            p1 = cqlengine.Text(partition_key=True)
            p2 = cqlengine.Text(partition_key=True)

        cols = ModelWithPartitionKeys._columns

        self.assertTrue(cols['c1'].primary_key)
        self.assertFalse(cols['c1'].partition_key)

        self.assertTrue(cols['p1'].primary_key)
        self.assertTrue(cols['p1'].partition_key)
        self.assertTrue(cols['p2'].primary_key)
        self.assertTrue(cols['p2'].partition_key)

        obj = ModelWithPartitionKeys(p1='a', p2='b')
        self.assertEquals(obj.pk, ('a', 'b'))

    def test_del_attribute_is_assigned_properly(self):
        """ Tests that columns that can be deleted have the del attribute """
        class DelModel(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())
            key = columns.Integer(primary_key=True)
            data = columns.Integer(required=False)

        model = DelModel(key=4, data=5)
        del model.data
        with self.assertRaises(AttributeError):
            del model.key

    def test_does_not_exist_exceptions_are_not_shared_between_model(self):
        """ Tests that DoesNotExist exceptions are not the same exception between models """

        class Model1(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())

        class Model2(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())

        try:
            raise Model1.DoesNotExist
        except Model2.DoesNotExist:
            assert False, "Model1 exception should not be caught by Model2"
        except Model1.DoesNotExist:
            #expected
            pass

    def test_does_not_exist_inherits_from_superclass(self):
        """ Tests that a DoesNotExist exception can be caught by it's parent class DoesNotExist """
        class Model1(Model):
            id  = columns.UUID(primary_key=True, default=lambda:uuid4())

        class Model2(Model1):
            pass

        try:
            raise Model2.DoesNotExist
        except Model1.DoesNotExist:
            #expected
            pass
        except Exception:
            assert False, "Model2 exception should not be caught by Model1"

class TestManualTableNaming(BaseCassEngTestCase):

    class RenamedTest(cqlengine.Model):
        __keyspace__ = 'whatever'
        __table_name__ = 'manual_name'

        id = cqlengine.UUID(primary_key=True)
        data = cqlengine.Text()

    def test_proper_table_naming(self):
        assert self.RenamedTest.column_family_name(include_keyspace=False) == 'manual_name'
        assert self.RenamedTest.column_family_name(include_keyspace=True) == 'whatever.manual_name'

class AbstractModel(Model):
    __abstract__ = True

class ConcreteModel(AbstractModel):
    pkey = columns.Integer(primary_key=True)
    data = columns.Integer()

class AbstractModelWithCol(Model):
    __abstract__ = True
    pkey = columns.Integer(primary_key=True)

class ConcreteModelWithCol(AbstractModelWithCol):
    data = columns.Integer()

class AbstractModelWithFullCols(Model):
    __abstract__ = True
    pkey = columns.Integer(primary_key=True)
    data = columns.Integer()

class TestAbstractModelClasses(BaseCassEngTestCase):

    def test_id_field_is_not_created(self):
        """ Tests that an id field is not automatically generated on abstract classes """
        assert not hasattr(AbstractModel, 'id')
        assert not hasattr(AbstractModelWithCol, 'id')

    def test_id_field_is_not_created_on_subclass(self):
        assert not hasattr(ConcreteModel, 'id')

    def test_abstract_attribute_is_not_inherited(self):
        """ Tests that __abstract__ attribute is not inherited """
        assert not ConcreteModel.__abstract__
        assert not ConcreteModelWithCol.__abstract__

    def test_attempting_to_save_abstract_model_fails(self):
        """ Attempting to save a model from an abstract model should fail """
        with self.assertRaises(CQLEngineException):
            AbstractModelWithFullCols.create(pkey=1, data=2)

    def test_attempting_to_create_abstract_table_fails(self):
        """ Attempting to create a table from an abstract model should fail """
        from cqlengine.management import create_table
        with self.assertRaises(CQLEngineException):
            create_table(AbstractModelWithFullCols)

    def test_attempting_query_on_abstract_model_fails(self):
        """ Tests attempting to execute query with an abstract model fails """
        with self.assertRaises(CQLEngineException):
            iter(AbstractModelWithFullCols.objects(pkey=5)).next()

    def test_abstract_columns_are_inherited(self):
        """ Tests that columns defined in the abstract class are inherited into the concrete class """
        assert hasattr(ConcreteModelWithCol, 'pkey')
        assert isinstance(ConcreteModelWithCol.pkey, ColumnQueryEvaluator)
        assert isinstance(ConcreteModelWithCol._columns['pkey'], columns.Column)

    def test_concrete_class_table_creation_cycle(self):
        """ Tests that models with inherited abstract classes can be created, and have io performed """
        from cqlengine.management import create_table, delete_table
        create_table(ConcreteModelWithCol)

        w1 = ConcreteModelWithCol.create(pkey=5, data=6)
        w2 = ConcreteModelWithCol.create(pkey=6, data=7)

        r1 = ConcreteModelWithCol.get(pkey=5)
        r2 = ConcreteModelWithCol.get(pkey=6)

        assert w1.pkey == r1.pkey
        assert w1.data == r1.data
        assert w2.pkey == r2.pkey
        assert w2.data == r2.data

        delete_table(ConcreteModelWithCol)


class TestCustomQuerySet(BaseCassEngTestCase):
    """ Tests overriding the default queryset class """

    class TestException(Exception): pass

    def test_overriding_queryset(self):

        class QSet(ModelQuerySet):
            def create(iself, **kwargs):
                raise self.TestException

        class CQModel(Model):
            __queryset__ = QSet
            part = columns.UUID(primary_key=True)
            data = columns.Text()

        with self.assertRaises(self.TestException):
            CQModel.create(part=uuid4(), data='s')

    def test_overriding_dmlqueryset(self):

        class DMLQ(DMLQuery):
            def save(iself):
                raise self.TestException

        class CDQModel(Model):
            __dmlquery__ = DMLQ
            part = columns.UUID(primary_key=True)
            data = columns.Text()

        with self.assertRaises(self.TestException):
            CDQModel().save()










