from unittest import TestCase
from cqlengine import connection
import os


if os.environ.get('CASSANDRA_TEST_HOST'):
    CASSANDRA_TEST_HOST = os.environ['CASSANDRA_TEST_HOST']
else:
    CASSANDRA_TEST_HOST = 'localhost:9160'


class BaseCassEngTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseCassEngTestCase, cls).setUpClass()
        connection.setup([CASSANDRA_TEST_HOST], default_keyspace='cqlengine_test')

    def assertHasAttr(self, obj, attr):
        self.assertTrue(hasattr(obj, attr),
                "{} doesn't have attribute: {}".format(obj, attr))

    def assertNotHasAttr(self, obj, attr):
        self.assertFalse(hasattr(obj, attr),
                "{} shouldn't have the attribute: {}".format(obj, attr))
