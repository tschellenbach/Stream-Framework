from __future__ import division

import unittest
from datetime import datetime
import mock

from stream_framework.utils import chunks, warn_on_duplicate, make_list_unique, \
    warn_on_error, datetime_to_epoch, epoch_to_datetime
from stream_framework.exceptions import DuplicateActivityException


class ChunksTest(unittest.TestCase):

    def test_chunks(self):
        chunked = chunks(range(6), 2)
        chunked = list(chunked)
        self.assertEqual(chunked, [(0, 1), (2, 3), (4, 5)])

    def test_one_chunk(self):
        chunked = chunks(range(2), 5)
        chunked = list(chunked)
        self.assertEqual(chunked, [(0, 1)])


def safe_function():
    return 10


def evil_duplicate():
    raise DuplicateActivityException('test')


def evil_value():
    raise ValueError('test')


class WarnTest(unittest.TestCase):

    def test_warn(self):
        # this should raise an error
        self.assertRaises(ValueError, evil_value)
        with mock.patch('stream_framework.utils.logger.warn') as warn:
            # this shouldnt raise an error
            wrapped = warn_on_error(evil_value, (ValueError,))
            wrapped()
        # but stick something in the log
        assert warn.called

    def test_warn_on_duplicate(self):
        # this should raise an error
        self.assertRaises(DuplicateActivityException, evil_duplicate)
        # this shouldnt raise an error
        with mock.patch('stream_framework.utils.logger.warn') as warn:
            wrapped = warn_on_duplicate(evil_duplicate)
            wrapped()
        # but stick something in the log
        assert warn.called


class UniqueListTest(unittest.TestCase):

    def test_make_list_unique(self):
        with_doubles = list(range(10)) + list(range(5, 15))
        result = make_list_unique(with_doubles)
        assert result == list(range(15))

    def test_make_list_unique_marker(self):
        with_doubles = list(range(10)) + list(range(5, 15))
        marker = lambda x: x // 5
        result = make_list_unique(with_doubles, marker)
        assert result == [0, 5, 10]


class DatetimeConversionTest(unittest.TestCase):

    def test_conversion(self):
        source_date = datetime.now()
        epoch = datetime_to_epoch(source_date)
        converted_date = epoch_to_datetime(epoch)

        assert source_date == converted_date

