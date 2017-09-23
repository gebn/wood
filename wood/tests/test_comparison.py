# -*- coding: utf-8 -*-
import unittest

from wood.entities import File, Directory, Root
from wood.comparison import Comparison


class TestComparison(unittest.TestCase):

    def test_directory_not_removed(self):
        a = Directory('assets', {
            'css': Directory('css', {
                'styles.css': File('styles.css', 1, 'abc')
            }),
            'img': Directory('img', {
                'george.jpg': File('george.jpg', 12345, 'abc')
            })
        })
        b = Directory('assets', {
            'css': Directory('css', {
                'styles.css': File('styles.css', 1, 'abcd')
            }),
            'img': Directory('img', {
                'george.jpg': File('george.jpg', 12345, 'abc')
            })
        })
        comparison = Comparison.compare(b, a)
        self.assertListEqual(list(comparison.invalidations()),
                             ['assets/css/*'])

    def test_add_delete(self):
        a = Root({
            'd1': Directory('d1', {
                'f1': File('f1', 1, ''),
                'f2': File('f2', 1, '')
            }),
            'd2': Directory('d2', {
                'f3': File('f3', 1, ''),
                'f4': File('f4', 1, '')
            }),
            'd3': Directory('d3', {
                'f5': File('f5', 1, '')
            }),
            'f6': File('f6', 1, ''),
            'f7': File('f7', 1, '')
        })
        b = Root({
            'd1': Directory('d1', {
                # deleted file d1/f1
                'f2': File('f2', 1, ''),
                'f9': File('f9', 1, ''),  # added file d1/f9
                'd4': Directory('d4')  # added dir d1/d4
            }),
            # removed dir d2 with files d2/f3 and d2/f4
            'd3': File('d3', 1, ''),  # added file d3, which was a directory;
            #                           old d3 and d3/f5 implicitly deleted
            'd5': Directory('d5', {  # added dir d5
                'f10': File('f10', 1, ''),  # added file d5/f10
                'f11': File('f11', 1, '')  # added file d5/f11
            }),
            'f6': Directory('f6', {  # added dir f6, which was a file; old f6
                #                      implicitly deleted
                'f12': File('f12', 1, '')  # added file f6/f12
            }),
            'f7': File('f7', 1, '')
        })
        comparison = Comparison.compare(a, b)
        self.assertSetEqual(set(comparison.new()),
                            {'d1/f9', 'd1/d4/', 'd3', 'd5/', 'd5/f10',
                             'd5/f11', 'f6/', 'f6/f12'})
        self.assertSetEqual(set(comparison.deleted()),
                            {'d1/f1', 'd2/', 'd2/f3', 'd2/f4', 'd3/', 'd3/f5',
                             'f6'})
