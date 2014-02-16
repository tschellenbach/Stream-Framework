from datetime import datetime
import time

from cqlengine.tests.base import BaseCassEngTestCase
from cqlengine import columns, Model
from cqlengine import functions
from cqlengine import query

class TestQuerySetOperation(BaseCassEngTestCase):

    def test_maxtimeuuid_function(self):
        """
        Tests that queries with helper functions are generated properly
        """
        now = datetime.now()
        col = columns.DateTime()
        col.set_column_name('time')
        qry = query.EqualsOperator(col, functions.MaxTimeUUID(now))

        assert qry.cql == '"time" = MaxTimeUUID(:{})'.format(qry.value.identifier)

    def test_mintimeuuid_function(self):
        """
        Tests that queries with helper functions are generated properly
        """
        now = datetime.now()
        col = columns.DateTime()
        col.set_column_name('time')
        qry = query.EqualsOperator(col, functions.MinTimeUUID(now))

        assert qry.cql == '"time" = MinTimeUUID(:{})'.format(qry.value.identifier)

    def test_token_function(self):

        class TestModel(Model):
            p1 = columns.Text(partition_key=True)
            p2 = columns.Text(partition_key=True)

        func = functions.Token('a', 'b')

        q = TestModel.objects.filter(pk__token__gt=func)
        self.assertEquals(q._where[0].cql, 'token("p1", "p2") > token(:{}, :{})'.format(*func.identifier))

        # Token(tuple()) is also possible for convinience
        # it (allows for Token(obj.pk) syntax)
        func = functions.Token(('a', 'b'))

        q = TestModel.objects.filter(pk__token__gt=func)
        self.assertEquals(q._where[0].cql, 'token("p1", "p2") > token(:{}, :{})'.format(*func.identifier))

