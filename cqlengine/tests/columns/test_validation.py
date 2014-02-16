#tests the behavior of the column classes
from datetime import datetime, timedelta
from datetime import date
from datetime import tzinfo
from decimal import Decimal as D
from unittest import TestCase
from uuid import uuid4, uuid1
from cqlengine import ValidationError

from cqlengine.tests.base import BaseCassEngTestCase

from cqlengine.columns import Column, TimeUUID
from cqlengine.columns import Bytes
from cqlengine.columns import Ascii
from cqlengine.columns import Text
from cqlengine.columns import Integer
from cqlengine.columns import VarInt
from cqlengine.columns import DateTime
from cqlengine.columns import Date
from cqlengine.columns import UUID
from cqlengine.columns import Boolean
from cqlengine.columns import Float
from cqlengine.columns import Decimal

from cqlengine.management import create_table, delete_table
from cqlengine.models import Model

import sys


class TestDatetime(BaseCassEngTestCase):
    class DatetimeTest(Model):
        test_id = Integer(primary_key=True)
        created_at = DateTime()

    @classmethod
    def setUpClass(cls):
        super(TestDatetime, cls).setUpClass()
        create_table(cls.DatetimeTest)

    @classmethod
    def tearDownClass(cls):
        super(TestDatetime, cls).tearDownClass()
        delete_table(cls.DatetimeTest)

    def test_datetime_io(self):
        now = datetime.now()
        dt = self.DatetimeTest.objects.create(test_id=0, created_at=now)
        dt2 = self.DatetimeTest.objects(test_id=0).first()
        assert dt2.created_at.timetuple()[:6] == now.timetuple()[:6]

    def test_datetime_tzinfo_io(self):
        class TZ(tzinfo):
            def utcoffset(self, date_time):
                return timedelta(hours=-1)
            def dst(self, date_time):
                return None

        now = datetime(1982, 1, 1, tzinfo=TZ())
        dt = self.DatetimeTest.objects.create(test_id=0, created_at=now)
        dt2 = self.DatetimeTest.objects(test_id=0).first()
        assert dt2.created_at.timetuple()[:6] == (now + timedelta(hours=1)).timetuple()[:6]

    def test_datetime_date_support(self):
        today = date.today()
        self.DatetimeTest.objects.create(test_id=0, created_at=today)
        dt2 = self.DatetimeTest.objects(test_id=0).first()
        assert dt2.created_at.isoformat() == datetime(today.year, today.month, today.day).isoformat()


class TestVarInt(BaseCassEngTestCase):
    class VarIntTest(Model):
        test_id = Integer(primary_key=True)
        bignum = VarInt(primary_key=True)

    @classmethod
    def setUpClass(cls):
        super(TestVarInt, cls).setUpClass()
        create_table(cls.VarIntTest)

    @classmethod
    def tearDownClass(cls):
        super(TestVarInt, cls).tearDownClass()
        delete_table(cls.VarIntTest)

    def test_varint_io(self):
        long_int = sys.maxint + 1
        int1 = self.VarIntTest.objects.create(test_id=0, bignum=long_int)
        int2 = self.VarIntTest.objects(test_id=0).first()
        assert int1.bignum == int2.bignum


class TestDate(BaseCassEngTestCase):
    class DateTest(Model):
        test_id = Integer(primary_key=True)
        created_at = Date()

    @classmethod
    def setUpClass(cls):
        super(TestDate, cls).setUpClass()
        create_table(cls.DateTest)

    @classmethod
    def tearDownClass(cls):
        super(TestDate, cls).tearDownClass()
        delete_table(cls.DateTest)

    def test_date_io(self):
        today = date.today()
        self.DateTest.objects.create(test_id=0, created_at=today)
        dt2 = self.DateTest.objects(test_id=0).first()
        assert dt2.created_at.isoformat() == today.isoformat()

    def test_date_io_using_datetime(self):
        now = datetime.utcnow()
        self.DateTest.objects.create(test_id=0, created_at=now)
        dt2 = self.DateTest.objects(test_id=0).first()
        assert not isinstance(dt2.created_at, datetime)
        assert isinstance(dt2.created_at, date)
        assert dt2.created_at.isoformat() == now.date().isoformat()


class TestDecimal(BaseCassEngTestCase):
    class DecimalTest(Model):
        test_id = Integer(primary_key=True)
        dec_val = Decimal()

    @classmethod
    def setUpClass(cls):
        super(TestDecimal, cls).setUpClass()
        create_table(cls.DecimalTest)

    @classmethod
    def tearDownClass(cls):
        super(TestDecimal, cls).tearDownClass()
        delete_table(cls.DecimalTest)

    def test_decimal_io(self):
        dt = self.DecimalTest.objects.create(test_id=0, dec_val=D('0.00'))
        dt2 = self.DecimalTest.objects(test_id=0).first()
        assert dt2.dec_val == dt.dec_val

        dt = self.DecimalTest.objects.create(test_id=0, dec_val=5)
        dt2 = self.DecimalTest.objects(test_id=0).first()
        assert dt2.dec_val == D('5')

class TestTimeUUID(BaseCassEngTestCase):
    class TimeUUIDTest(Model):
        test_id = Integer(primary_key=True)
        timeuuid = TimeUUID(default=uuid1())

    @classmethod
    def setUpClass(cls):
        super(TestTimeUUID, cls).setUpClass()
        create_table(cls.TimeUUIDTest)

    @classmethod
    def tearDownClass(cls):
        super(TestTimeUUID, cls).tearDownClass()
        delete_table(cls.TimeUUIDTest)

    def test_timeuuid_io(self):
        """
        ensures that
        :return:
        """
        t0 = self.TimeUUIDTest.create(test_id=0)
        t1 = self.TimeUUIDTest.get(test_id=0)

        assert t1.timeuuid.time == t1.timeuuid.time

class TestInteger(BaseCassEngTestCase):
    class IntegerTest(Model):
        test_id = UUID(primary_key=True, default=lambda:uuid4())
        value   = Integer(default=0, required=True)

    def test_default_zero_fields_validate(self):
        """ Tests that integer columns with a default value of 0 validate """
        it = self.IntegerTest()
        it.validate()

class TestText(BaseCassEngTestCase):

    def test_min_length(self):
        #min len defaults to 1
        col = Text()
        col.validate('')

        col.validate('b')

        #test not required defaults to 0
        Text(required=False).validate('')

        #test arbitrary lengths
        Text(min_length=0).validate('')
        Text(min_length=5).validate('blake')
        Text(min_length=5).validate('blaketastic')
        with self.assertRaises(ValidationError):
            Text(min_length=6).validate('blake')

    def test_max_length(self):

        Text(max_length=5).validate('blake')
        with self.assertRaises(ValidationError):
            Text(max_length=5).validate('blaketastic')

    def test_type_checking(self):
        Text().validate('string')
        Text().validate(u'unicode')
        Text().validate(bytearray('bytearray'))

        with self.assertRaises(ValidationError):
            Text(required=True).validate(None)

        with self.assertRaises(ValidationError):
            Text().validate(5)

        with self.assertRaises(ValidationError):
            Text().validate(True)

    def test_non_required_validation(self):
        """ Tests that validation is ok on none and blank values if required is False """
        Text().validate('')
        Text().validate(None)




class TestExtraFieldsRaiseException(BaseCassEngTestCase):
    class TestModel(Model):
        id = UUID(primary_key=True, default=uuid4)

    def test_extra_field(self):
        with self.assertRaises(ValidationError):
            self.TestModel.create(bacon=5000)


class TestTimeUUIDFromDatetime(TestCase):
    def test_conversion_specific_date(self):
        dt = datetime(1981, 7, 11, microsecond=555000)

        uuid = TimeUUID.from_datetime(dt)

        from uuid import UUID
        assert isinstance(uuid, UUID)

        ts = (uuid.time - 0x01b21dd213814000) / 1e7 # back to a timestamp
        new_dt = datetime.utcfromtimestamp(ts)

        # checks that we created a UUID1 with the proper timestamp
        assert new_dt == dt

