from uuid import uuid4
import random
from cqlengine.tests.base import BaseCassEngTestCase

from cqlengine.management import create_table
from cqlengine.management import delete_table
from cqlengine.models import Model
from cqlengine import columns

class TestModel(Model):
    id      = columns.UUID(primary_key=True, default=lambda:uuid4())
    count   = columns.Integer()
    text    = columns.Text(required=False)
    a_bool  = columns.Boolean(default=False)

class TestModel(Model):
    id      = columns.UUID(primary_key=True, default=lambda:uuid4())
    count   = columns.Integer()
    text    = columns.Text(required=False)
    a_bool  = columns.Boolean(default=False)


class TestModelIO(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestModelIO, cls).setUpClass()
        create_table(TestModel)

    @classmethod
    def tearDownClass(cls):
        super(TestModelIO, cls).tearDownClass()
        delete_table(TestModel)

    def test_model_save_and_load(self):
        """
        Tests that models can be saved and retrieved
        """
        tm = TestModel.create(count=8, text='123456789')
        tm2 = TestModel.objects(id=tm.pk).first()

        for cname in tm._columns.keys():
            self.assertEquals(getattr(tm, cname), getattr(tm2, cname))



    def test_model_updating_works_properly(self):
        """
        Tests that subsequent saves after initial model creation work
        """
        tm = TestModel.objects.create(count=8, text='123456789')

        tm.count = 100
        tm.a_bool = True
        tm.save()

        tm2 = TestModel.objects(id=tm.pk).first()
        self.assertEquals(tm.count, tm2.count)
        self.assertEquals(tm.a_bool, tm2.a_bool)

    def test_model_deleting_works_properly(self):
        """
        Tests that an instance's delete method deletes the instance
        """
        tm = TestModel.create(count=8, text='123456789')
        tm.delete()
        tm2 = TestModel.objects(id=tm.pk).first()
        self.assertIsNone(tm2)

    def test_column_deleting_works_properly(self):
        """
        """
        tm = TestModel.create(count=8, text='123456789')
        tm.text = None
        tm.save()

        tm2 = TestModel.objects(id=tm.pk).first()
        assert tm2.text is None
        assert tm2._values['text'].previous_value is None


    def test_a_sensical_error_is_raised_if_you_try_to_create_a_table_twice(self):
        """
        """
        create_table(TestModel)
        create_table(TestModel)


class TestMultiKeyModel(Model):
    partition   = columns.Integer(primary_key=True)
    cluster     = columns.Integer(primary_key=True)
    count       = columns.Integer(required=False)
    text        = columns.Text(required=False)

class TestDeleting(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestDeleting, cls).setUpClass()
        delete_table(TestMultiKeyModel)
        create_table(TestMultiKeyModel)

    @classmethod
    def tearDownClass(cls):
        super(TestDeleting, cls).tearDownClass()
        delete_table(TestMultiKeyModel)

    def test_deleting_only_deletes_one_object(self):
        partition = random.randint(0,1000)
        for i in range(5):
            TestMultiKeyModel.create(partition=partition, cluster=i, count=i, text=str(i))

        assert TestMultiKeyModel.filter(partition=partition).count() == 5

        TestMultiKeyModel.get(partition=partition, cluster=0).delete()

        assert TestMultiKeyModel.filter(partition=partition).count() == 4

        TestMultiKeyModel.filter(partition=partition).delete()


class TestUpdating(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestUpdating, cls).setUpClass()
        delete_table(TestMultiKeyModel)
        create_table(TestMultiKeyModel)

    @classmethod
    def tearDownClass(cls):
        super(TestUpdating, cls).tearDownClass()
        delete_table(TestMultiKeyModel)

    def setUp(self):
        super(TestUpdating, self).setUp()
        self.instance = TestMultiKeyModel.create(
            partition=random.randint(0, 1000),
            cluster=random.randint(0, 1000),
            count=0,
            text='happy'
        )

    def test_vanilla_update(self):
        self.instance.count = 5
        self.instance.save()

        check = TestMultiKeyModel.get(partition=self.instance.partition, cluster=self.instance.cluster)
        assert check.count == 5
        assert check.text == 'happy'

    def test_deleting_only(self):
        self.instance.count = None
        self.instance.text = None
        self.instance.save()

        check = TestMultiKeyModel.get(partition=self.instance.partition, cluster=self.instance.cluster)
        assert check.count is None
        assert check.text is None



class TestCanUpdate(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCanUpdate, cls).setUpClass()
        delete_table(TestModel)
        create_table(TestModel)

    @classmethod
    def tearDownClass(cls):
        super(TestCanUpdate, cls).tearDownClass()
        delete_table(TestModel)

    def test_success_case(self):
        tm = TestModel(count=8, text='123456789')

        # object hasn't been saved,
        # shouldn't be able to update
        assert not tm._is_persisted
        assert not tm._can_update()

        tm.save()

        # object has been saved,
        # should be able to update
        assert tm._is_persisted
        assert tm._can_update()

        tm.count = 200

        # primary keys haven't changed,
        # should still be able to update
        assert tm._can_update()
        tm.save()

        tm.id = uuid4()

        # primary keys have changed,
        # should not be able to update
        assert not tm._can_update()


class IndexDefinitionModel(Model):
    key     = columns.UUID(primary_key=True)
    val     = columns.Text(index=True)

class TestIndexedColumnDefinition(BaseCassEngTestCase):

    def test_exception_isnt_raised_if_an_index_is_defined_more_than_once(self):
        create_table(IndexDefinitionModel)
        create_table(IndexDefinitionModel)

class ReservedWordModel(Model):
    token   = columns.Text(primary_key=True)
    insert  = columns.Integer(index=True)

class TestQueryQuoting(BaseCassEngTestCase):

    def test_reserved_cql_words_can_be_used_as_column_names(self):
        """
        """
        create_table(ReservedWordModel)

        model1 = ReservedWordModel.create(token='1', insert=5)

        model2 = ReservedWordModel.filter(token='1')

        assert len(model2) == 1
        assert model1.token == model2[0].token
        assert model1.insert == model2[0].insert


