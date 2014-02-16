from datetime import datetime
from unittest import skip
from uuid import uuid4
import random
from cqlengine import Model, columns
from cqlengine.management import delete_table, create_table
from cqlengine.query import BatchQuery, DMLQuery
from cqlengine.tests.base import BaseCassEngTestCase

class TestMultiKeyModel(Model):
    partition   = columns.Integer(primary_key=True)
    cluster     = columns.Integer(primary_key=True)
    count       = columns.Integer(required=False)
    text        = columns.Text(required=False)

class BatchQueryTests(BaseCassEngTestCase):

    @classmethod
    def setUpClass(cls):
        super(BatchQueryTests, cls).setUpClass()
        delete_table(TestMultiKeyModel)
        create_table(TestMultiKeyModel)

    @classmethod
    def tearDownClass(cls):
        super(BatchQueryTests, cls).tearDownClass()
        delete_table(TestMultiKeyModel)

    def setUp(self):
        super(BatchQueryTests, self).setUp()
        self.pkey = 1
        for obj in TestMultiKeyModel.filter(partition=self.pkey):
            obj.delete()

    def test_insert_success_case(self):

        b = BatchQuery()
        inst = TestMultiKeyModel.batch(b).create(partition=self.pkey, cluster=2, count=3, text='4')

        with self.assertRaises(TestMultiKeyModel.DoesNotExist):
            TestMultiKeyModel.get(partition=self.pkey, cluster=2)

        b.execute()

        TestMultiKeyModel.get(partition=self.pkey, cluster=2)

    def test_update_success_case(self):

        inst = TestMultiKeyModel.create(partition=self.pkey, cluster=2, count=3, text='4')

        b = BatchQuery()

        inst.count = 4
        inst.batch(b).save()

        inst2 = TestMultiKeyModel.get(partition=self.pkey, cluster=2)
        assert inst2.count == 3

        b.execute()

        inst3 = TestMultiKeyModel.get(partition=self.pkey, cluster=2)
        assert inst3.count == 4

    def test_delete_success_case(self):

        inst = TestMultiKeyModel.create(partition=self.pkey, cluster=2, count=3, text='4')

        b = BatchQuery()

        inst.batch(b).delete()

        TestMultiKeyModel.get(partition=self.pkey, cluster=2)

        b.execute()

        with self.assertRaises(TestMultiKeyModel.DoesNotExist):
            TestMultiKeyModel.get(partition=self.pkey, cluster=2)

    def test_context_manager(self):

        with BatchQuery() as b:
            for i in range(5):
                TestMultiKeyModel.batch(b).create(partition=self.pkey, cluster=i, count=3, text='4')

            for i in range(5):
                with self.assertRaises(TestMultiKeyModel.DoesNotExist):
                    TestMultiKeyModel.get(partition=self.pkey, cluster=i)

        for i in range(5):
            TestMultiKeyModel.get(partition=self.pkey, cluster=i)

    def test_bulk_delete_success_case(self):

        for i in range(1):
            for j in range(5):
                TestMultiKeyModel.create(partition=i, cluster=j, count=i*j, text='{}:{}'.format(i,j))

        with BatchQuery() as b:
            TestMultiKeyModel.objects.batch(b).filter(partition=0).delete()
            assert TestMultiKeyModel.filter(partition=0).count() == 5

        assert TestMultiKeyModel.filter(partition=0).count() == 0
        #cleanup
        for m in TestMultiKeyModel.all():
            m.delete()

    def test_none_success_case(self):
        """ Tests that passing None into the batch call clears any batch object """
        b = BatchQuery()

        q = TestMultiKeyModel.objects.batch(b)
        assert q._batch == b

        q = q.batch(None)
        assert q._batch is None

    def test_dml_none_success_case(self):
        """ Tests that passing None into the batch call clears any batch object """
        b = BatchQuery()

        q = DMLQuery(TestMultiKeyModel, batch=b)
        assert q._batch == b

        q.batch(None)
        assert q._batch is None
