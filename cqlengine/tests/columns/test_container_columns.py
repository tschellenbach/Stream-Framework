from datetime import datetime, timedelta
import json
from uuid import uuid4

from cqlengine import Model, ValidationError
from cqlengine import columns
from cqlengine.management import create_table, delete_table
from cqlengine.tests.base import BaseCassEngTestCase


class TestSetModel(Model):
    partition = columns.UUID(primary_key=True, default=uuid4)
    int_set = columns.Set(columns.Integer, required=False)
    text_set = columns.Set(columns.Text, required=False)


class JsonTestColumn(columns.Column):
    db_type = 'text'

    def to_python(self, value):
        if value is None:
            return
        if isinstance(value, basestring):
            return json.loads(value)
        else:
            return value

    def to_database(self, value):
        if value is None:
            return
        return json.dumps(value)


class TestSetColumn(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSetColumn, cls).setUpClass()
        delete_table(TestSetModel)
        create_table(TestSetModel)

    @classmethod
    def tearDownClass(cls):
        super(TestSetColumn, cls).tearDownClass()
        delete_table(TestSetModel)

    def test_empty_set_initial(self):
        """
        tests that sets are set() by default, should never be none
        :return:
        """
        m = TestSetModel.create()
        m.int_set.add(5)
        m.save()

    def test_empty_set_retrieval(self):
        m = TestSetModel.create()
        m2 = TestSetModel.get(partition=m.partition)
        m2.int_set.add(3)

    def test_io_success(self):
        """ Tests that a basic usage works as expected """
        m1 = TestSetModel.create(int_set={1, 2}, text_set={'kai', 'andreas'})
        m2 = TestSetModel.get(partition=m1.partition)

        assert isinstance(m2.int_set, set)
        assert isinstance(m2.text_set, set)

        assert 1 in m2.int_set
        assert 2 in m2.int_set

        assert 'kai' in m2.text_set
        assert 'andreas' in m2.text_set

    def test_type_validation(self):
        """
        Tests that attempting to use the wrong types will raise an exception
        """
        with self.assertRaises(ValidationError):
            TestSetModel.create(int_set={'string', True}, text_set={1, 3.0})

    def test_partial_updates(self):
        """ Tests that partial udpates work as expected """
        m1 = TestSetModel.create(int_set={1, 2, 3, 4})

        m1.int_set.add(5)
        m1.int_set.remove(1)
        assert m1.int_set == {2, 3, 4, 5}

        m1.save()

        m2 = TestSetModel.get(partition=m1.partition)
        assert m2.int_set == {2, 3, 4, 5}

    def test_partial_update_creation(self):
        """
        Tests that proper update statements are created for a partial set update
        :return:
        """
        ctx = {}
        col = columns.Set(columns.Integer, db_field="TEST")
        statements = col.get_update_statement({1, 2, 3, 4}, {2, 3, 4, 5}, ctx)

        assert len([v for v in ctx.values() if {1} == v.value]) == 1
        assert len([v for v in ctx.values() if {5} == v.value]) == 1
        assert len([s for s in statements if '"TEST" = "TEST" -' in s]) == 1
        assert len([s for s in statements if '"TEST" = "TEST" +' in s]) == 1

    def test_update_from_none(self):
        """ Tests that updating an 'None' list creates a straight insert statement """
        ctx = {}
        col = columns.Set(columns.Integer, db_field="TEST")
        statements = col.get_update_statement({1, 2, 3, 4}, None, ctx)

        # only one variable /statement should be generated
        assert len(ctx) == 1
        assert len(statements) == 1

        assert ctx.values()[0].value == {1, 2, 3, 4}
        assert statements[0] == '"TEST" = {{}}'.format(ctx.keys()[0])

    def test_update_from_empty(self):
        """ Tests that updating an empty list creates a straight insert statement """
        ctx = {}
        col = columns.Set(columns.Integer, db_field="TEST")
        statements = col.get_update_statement({1, 2, 3, 4}, set(), ctx)

        # only one variable /statement should be generated
        assert len(ctx) == 1
        assert len(statements) == 1

        assert ctx.values()[0].value == {1, 2, 3, 4}
        assert statements[0] == '"TEST" = {{}}'.format(ctx.keys()[0])

    def test_instantiation_with_column_class(self):
        """
        Tests that columns instantiated with a column class work properly
        and that the class is instantiated in the constructor
        """
        column = columns.Set(columns.Text)
        assert isinstance(column.value_col, columns.Text)

    def test_instantiation_with_column_instance(self):
        """
        Tests that columns instantiated with a column instance work properly
        """
        column = columns.Set(columns.Text(min_length=100))
        assert isinstance(column.value_col, columns.Text)

    def test_to_python(self):
        """ Tests that to_python of value column is called """
        column = columns.Set(JsonTestColumn)
        val = {1, 2, 3}
        db_val = column.to_database(val)
        assert db_val.value == {json.dumps(v) for v in val}
        py_val = column.to_python(db_val.value)
        assert py_val == val


class TestListModel(Model):
    partition = columns.UUID(primary_key=True, default=uuid4)
    int_list = columns.List(columns.Integer, required=False)
    text_list = columns.List(columns.Text, required=False)


class TestListColumn(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestListColumn, cls).setUpClass()
        delete_table(TestListModel)
        create_table(TestListModel)

    @classmethod
    def tearDownClass(cls):
        super(TestListColumn, cls).tearDownClass()
        delete_table(TestListModel)

    def test_initial(self):
        tmp = TestListModel.create()
        tmp.int_list.append(1)

    def test_initial(self):
        tmp = TestListModel.create()
        tmp2 = TestListModel.get(partition=tmp.partition)
        tmp2.int_list.append(1)

    def test_io_success(self):
        """ Tests that a basic usage works as expected """
        m1 = TestListModel.create(
            int_list=[1, 2], text_list=['kai', 'andreas'])
        m2 = TestListModel.get(partition=m1.partition)

        assert isinstance(m2.int_list, list)
        assert isinstance(m2.text_list, list)

        assert len(m2.int_list) == 2
        assert len(m2.text_list) == 2

        assert m2.int_list[0] == 1
        assert m2.int_list[1] == 2

        assert m2.text_list[0] == 'kai'
        assert m2.text_list[1] == 'andreas'

    def test_type_validation(self):
        """
        Tests that attempting to use the wrong types will raise an exception
        """
        with self.assertRaises(ValidationError):
            TestListModel.create(int_list=['string', True], text_list=[1, 3.0])

    def test_partial_updates(self):
        """ Tests that partial udpates work as expected """
        final = range(10)
        initial = final[3:7]
        m1 = TestListModel.create(int_list=initial)

        m1.int_list = final
        m1.save()

        m2 = TestListModel.get(partition=m1.partition)
        assert list(m2.int_list) == final

    def test_partial_update_creation(self):
        """ Tests that proper update statements are created for a partial list update """
        final = range(10)
        initial = final[3:7]

        ctx = {}
        col = columns.List(columns.Integer, db_field="TEST")
        statements = col.get_update_statement(final, initial, ctx)

        assert len([v for v in ctx.values() if [2, 1, 0] == v.value]) == 1
        assert len([v for v in ctx.values() if [7, 8, 9] == v.value]) == 1
        assert len([s for s in statements if '"TEST" = "TEST" +' in s]) == 1
        assert len([s for s in statements if '+ "TEST"' in s]) == 1

    def test_update_from_none(self):
        """ Tests that updating an 'None' list creates a straight insert statement """
        ctx = {}
        col = columns.List(columns.Integer, db_field="TEST")
        statements = col.get_update_statement([1, 2, 3], None, ctx)

        # only one variable /statement should be generated
        assert len(ctx) == 1
        assert len(statements) == 1

        assert ctx.values()[0].value == [1, 2, 3]
        assert statements[0] == '"TEST" = {}'.format(ctx.keys()[0])

    def test_update_from_empty(self):
        """ Tests that updating an empty list creates a straight insert statement """
        ctx = {}
        col = columns.List(columns.Integer, db_field="TEST")
        statements = col.get_update_statement([1, 2, 3], [], ctx)

        # only one variable /statement should be generated
        assert len(ctx) == 1
        assert len(statements) == 1

        assert ctx.values()[0].value == [1, 2, 3]
        assert statements[0] == '"TEST" = {}'.format(ctx.keys()[0])

    def test_instantiation_with_column_class(self):
        """
        Tests that columns instantiated with a column class work properly
        and that the class is instantiated in the constructor
        """
        column = columns.List(columns.Text)
        assert isinstance(column.value_col, columns.Text)

    def test_instantiation_with_column_instance(self):
        """
        Tests that columns instantiated with a column instance work properly
        """
        column = columns.List(columns.Text(min_length=100))
        assert isinstance(column.value_col, columns.Text)

    def test_to_python(self):
        """ Tests that to_python of value column is called """
        column = columns.List(JsonTestColumn)
        val = [1, 2, 3]
        db_val = column.to_database(val)
        assert db_val.value == [json.dumps(v) for v in val]
        py_val = column.to_python(db_val.value)
        assert py_val == val


class TestMapModel(Model):
    partition = columns.UUID(primary_key=True, default=uuid4)
    int_map = columns.Map(columns.Integer, columns.UUID, required=False)
    text_map = columns.Map(columns.Text, columns.DateTime, required=False)


class TestMapColumn(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMapColumn, cls).setUpClass()
        delete_table(TestMapModel)
        create_table(TestMapModel)

    @classmethod
    def tearDownClass(cls):
        super(TestMapColumn, cls).tearDownClass()
        delete_table(TestMapModel)

    def test_empty_default(self):
        tmp = TestMapModel.create()
        tmp.int_map['blah'] = 1

    def test_empty_retrieve(self):
        tmp = TestMapModel.create()
        tmp2 = TestMapModel.get(partition=tmp.partition)
        tmp2.int_map['blah'] = 1

    def test_io_success(self):
        """ Tests that a basic usage works as expected """
        k1 = uuid4()
        k2 = uuid4()
        now = datetime.now()
        then = now + timedelta(days=1)
        m1 = TestMapModel.create(
            int_map={1: k1, 2: k2}, text_map={'now': now, 'then': then})
        m2 = TestMapModel.get(partition=m1.partition)

        assert isinstance(m2.int_map, dict)
        assert isinstance(m2.text_map, dict)

        assert 1 in m2.int_map
        assert 2 in m2.int_map
        assert m2.int_map[1] == k1
        assert m2.int_map[2] == k2

        assert 'now' in m2.text_map
        assert 'then' in m2.text_map
        assert (now - m2.text_map['now']).total_seconds() < 0.001
        assert (then - m2.text_map['then']).total_seconds() < 0.001

    def test_type_validation(self):
        """
        Tests that attempting to use the wrong types will raise an exception
        """
        with self.assertRaises(ValidationError):
            TestMapModel.create(
                int_map={'key': 2, uuid4(): 'val'}, text_map={2: 5})

    def test_partial_updates(self):
        """ Tests that partial udpates work as expected """
        now = datetime.now()
        # derez it a bit
        now = datetime(*now.timetuple()[:-3])
        early = now - timedelta(minutes=30)
        earlier = early - timedelta(minutes=30)
        later = now + timedelta(minutes=30)

        initial = {'now': now, 'early': earlier}
        final = {'later': later, 'early': early}

        m1 = TestMapModel.create(text_map=initial)

        m1.text_map = final
        m1.save()

        m2 = TestMapModel.get(partition=m1.partition)
        assert m2.text_map == final

    def test_updates_from_none(self):
        """ Tests that updates from None work as expected """
        m = TestMapModel.create(int_map=None)
        expected = {1: uuid4()}
        m.int_map = expected
        m.save()

        m2 = TestMapModel.get(partition=m.partition)
        assert m2.int_map == expected

    def test_updates_to_none(self):
        """ Tests that setting the field to None works as expected """
        m = TestMapModel.create(int_map={1: uuid4()})
        m.int_map = None
        m.save()

        m2 = TestMapModel.get(partition=m.partition)
        assert m2.int_map == {}

    def test_instantiation_with_column_class(self):
        """
        Tests that columns instantiated with a column class work properly
        and that the class is instantiated in the constructor
        """
        column = columns.Map(columns.Text, columns.Integer)
        assert isinstance(column.key_col, columns.Text)
        assert isinstance(column.value_col, columns.Integer)

    def test_instantiation_with_column_instance(self):
        """
        Tests that columns instantiated with a column instance work properly
        """
        column = columns.Map(columns.Text(min_length=100), columns.Integer())
        assert isinstance(column.key_col, columns.Text)
        assert isinstance(column.value_col, columns.Integer)

    def test_to_python(self):
        """ Tests that to_python of value column is called """
        column = columns.Map(JsonTestColumn, JsonTestColumn)
        val = {1: 2, 3: 4, 5: 6}
        db_val = column.to_database(val)
        assert db_val.value == {
            json.dumps(k): json.dumps(v) for k, v in val.items()}
        py_val = column.to_python(db_val.value)
        assert py_val == val

#    def test_partial_update_creation(self):
#        """
#        Tests that proper update statements are created for a partial list update
#        :return:
#        """
#        final = range(10)
#        initial = final[3:7]
#
#        ctx = {}
#        col = columns.List(columns.Integer, db_field="TEST")
#        statements = col.get_update_statement(final, initial, ctx)
#
#        assert len([v for v in ctx.values() if [0,1,2] == v.value]) == 1
#        assert len([v for v in ctx.values() if [7,8,9] == v.value]) == 1
#        assert len([s for s in statements if '"TEST" = "TEST" +' in s]) == 1
#        assert len([s for s in statements if '+ "TEST"' in s]) == 1
