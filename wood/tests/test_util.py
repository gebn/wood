# -*- coding: utf-8 -*-
import unittest

from wood import util


class TestZipDict(unittest.TestCase):

    def test_both_empty(self):
        self.assertDictEqual(util.zip_dict({}, {}), {})

    def test_one_empty(self):
        self.assertDictEqual(util.zip_dict({},
                                           {
                                               'a': '1',
                                               'b': 2
                                           }),
                             {
                                 'a': (None, '1'),
                                 'b': (None, 2)
                             })

    def test_success(self):
        self.assertDictEqual(util.zip_dict({
                                               'a': 1,
                                               'b': 2,
                                               'd': 3
                                           },
                                           {
                                               'a': 2,
                                               'c': 4,
                                               'd': 9
                                           }),
                             {
                                 'a': (1, 2),
                                 'b': (2, None),
                                 'c': (None, 4),
                                 'd': (3, 9)
                             })


class TestChunk(unittest.TestCase):

    @staticmethod
    def _listify(result):
        l = []
        for chunk in result:
            l.append(list(chunk))
        return l

    def test_empty(self):
        self.assertListEqual(TestChunk._listify(util.chunk([], 5)), [])

    def test_all_full(self):
        self.assertListEqual(TestChunk._listify(util.chunk(range(6), 2)),
                             [[0, 1], [2, 3], [4, 5]])

    def test_partial_full(self):
        self.assertListEqual(TestChunk._listify(util.chunk(range(4), 3)),
                             [[0, 1, 2], [3]])
