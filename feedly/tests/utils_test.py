import unittest
from feedly.utils import chunks


class ChunksTest(unittest.TestCase):

    def test_chunks(self):
        chunked = chunks(range(6), 2)
        chunked = list(chunked)
        self.assertEqual(chunked, [(0, 1), (2, 3), (4, 5)])

    def test_one_chunk(self):
        chunked = chunks(range(2), 5)
        chunked = list(chunked)
        self.assertEqual(chunked, [(0, 1)])

