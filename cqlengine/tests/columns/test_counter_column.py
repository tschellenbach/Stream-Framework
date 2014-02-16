from uuid import uuid4

from cqlengine import Model
from cqlengine import columns
from cqlengine.management import create_table, delete_table
from cqlengine.models import ModelDefinitionException
from cqlengine.tests.base import BaseCassEngTestCase


class TestCounterModel(Model):
    partition = columns.UUID(primary_key=True, default=uuid4)
    cluster = columns.UUID(primary_key=True, default=uuid4)
    counter = columns.Counter()


class TestClassConstruction(BaseCassEngTestCase):

    def test_defining_a_non_counter_column_fails(self):
        """ Tests that defining a non counter column field in a model with a counter column fails """
        with self.assertRaises(ModelDefinitionException):
            class model(Model):
                partition = columns.UUID(primary_key=True, default=uuid4)
                counter = columns.Counter()
                text = columns.Text()


    def test_defining_a_primary_key_counter_column_fails(self):
        """ Tests that defining primary keys on counter columns fails """
        with self.assertRaises(TypeError):
            class model(Model):
                partition = columns.UUID(primary_key=True, default=uuid4)
                cluster = columns.Counter(primary_ley=True)
                counter = columns.Counter()

        # force it
        with self.assertRaises(ModelDefinitionException):
            class model(Model):
                partition = columns.UUID(primary_key=True, default=uuid4)
                cluster = columns.Counter()
                cluster.primary_key = True
                counter = columns.Counter()


class TestCounterColumn(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCounterColumn, cls).setUpClass()
        delete_table(TestCounterModel)
        create_table(TestCounterModel)

    @classmethod
    def tearDownClass(cls):
        super(TestCounterColumn, cls).tearDownClass()
        delete_table(TestCounterModel)

    def test_updates(self):
        """ Tests that counter updates work as intended """
        instance = TestCounterModel.create()
        instance.counter += 5
        instance.save()

        actual = TestCounterModel.get(partition=instance.partition)
        assert actual.counter == 5

    def test_concurrent_updates(self):
        """ Tests updates from multiple queries reaches the correct value """
        instance = TestCounterModel.create()
        new1 = TestCounterModel.get(partition=instance.partition)
        new2 = TestCounterModel.get(partition=instance.partition)

        new1.counter += 5
        new1.save()
        new2.counter += 5
        new2.save()

        actual = TestCounterModel.get(partition=instance.partition)
        assert actual.counter == 10

    def test_update_from_none(self):
        """ Tests that updating from None uses a create statement """
        instance = TestCounterModel()
        instance.counter += 1
        instance.save()

        new = TestCounterModel.get(partition=instance.partition)
        assert new.counter == 1

    def test_new_instance_defaults_to_zero(self):
        """ Tests that instantiating a new model instance will set the counter column to zero """
        instance = TestCounterModel()
        assert instance.counter == 0

