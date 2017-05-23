# -*- coding: utf-8 -*-

import unittest

from kiwi.python import AttributeForwarder, slicerange, enum, strip_accents


class SliceTest(unittest.TestCase):
    def genlist(self, limit, start, stop=None, step=None):
        if stop is None:
            stop = start
            start = None

        return list(slicerange(slice(start, stop, step), limit))

    def testStop(self):
        self.assertEqual(self.genlist(10, 10), list(range(10)))
        self.assertEqual(self.genlist(10, -5), list(range(5)))
        self.assertEqual(self.genlist(10, -15), [])
        self.assertEqual(self.genlist(5, 10), list(range(5)))
        self.assertEqual(self.genlist(0, 10), [])

    def testStartStop(self):
        self.assertEqual(self.genlist(10, 0, 10), list(range(10)))
        self.assertEqual(self.genlist(10, 1, 9), list(range(10))[1:9])
        self.assertEqual(self.genlist(10, -1, -1), list(range(10))[-1:-1])
        self.assertEqual(self.genlist(10, 0, -15), list(range(10))[0:-15])
        self.assertEqual(self.genlist(10, 15, 0), list(range(10))[-15:0])

    def testStartStopStep(self):
        self.assertEqual(self.genlist(10, 0, 10, 2), list(range(10))[0:10:2])


class Status(enum):
    OPEN, CLOSE = range(2)


class Color(enum):
    RED, GREEN, BLUE = range(3)


class EnumTest(unittest.TestCase):
    def testEnums(self):
        self.assertTrue(issubclass(enum, int))
        self.assertTrue(isinstance(Color.RED, Color))
        self.assertTrue(isinstance(Color.RED, int))
        self.assertTrue('RED' in repr(Color.RED), repr(Color.RED))
        self.assertTrue(int(Color.RED) is not None)

    def testComparision(self):
        self.assertEqual(Color.RED, 0)
        self.assertNotEqual(Color.RED, 1)
        self.assertNotEqual(Color.RED, -1)
        self.assertNotEqual(Color.RED, Color.GREEN)
        self.assertNotEqual(Color.GREEN, Status.OPEN)

    def testGet(self):
        self.assertEqual(Color.get(0), Color.RED)
        self.assertRaises(ValueError, Color.get, 3)

    def testNew(self):
        yellow = Color(3, 'YELLOW')
        self.assertTrue(isinstance(yellow, Color))
        self.assertEqual(Color.YELLOW, yellow)
        self.assertRaises(ValueError, Color, 3, 'AGAIN')
        self.assertRaises(ValueError, Color, 4, 'RED')


class AttributeForwarderTest(unittest.TestCase):
    def testForward(self):
        class FW(AttributeForwarder):
            attributes = ['forward']

        class Target(object):
            forward = 'foo'

        target = Target()
        f = FW(target)
        self.assertEqual(f.target, target)
        self.assertEqual(f.forward, 'foo')
        f.forward = 'bar'
        self.assertEqual(target.forward, 'bar')
        self.assertEqual(f.forward, 'bar')


class StripAccentsTest(unittest.TestCase):
    def testStripAccents(self):
        for string, string_without_accentuation in [
            # bytes
            ('áâãäåāăąàÁÂÃÄÅĀĂĄÀ'.encode(), b'aaaaaaaaaAAAAAAAAA'),
            ('èééêëēĕėęěĒĔĖĘĚ'.encode(), b'eeeeeeeeeeEEEEE'),
            ('ìíîïìĩīĭÌÍÎÏÌĨĪĬ'.encode(), b'iiiiiiiiIIIIIIII'),
            ('óôõöōŏőÒÓÔÕÖŌŎŐ'.encode(), b'oooooooOOOOOOOO'),
            ('ùúûüũūŭůÙÚÛÜŨŪŬŮ'.encode(), b'uuuuuuuuUUUUUUUU'),
            ('çÇ'.encode(), b'cC'),
            # strings
            ('áâãäåāăąàÁÂÃÄÅĀĂĄÀ', 'aaaaaaaaaAAAAAAAAA'),
            ('èééêëēĕėęěĒĔĖĘĚ', 'eeeeeeeeeeEEEEE'),
            ('ìíîïìĩīĭÌÍÎÏÌĨĪĬ', 'iiiiiiiiIIIIIIII'),
            ('óôõöōŏőÒÓÔÕÖŌŎŐ', 'oooooooOOOOOOOO'),
            ('ùúûüũūŭůÙÚÛÜŨŪŬŮ', 'uuuuuuuuUUUUUUUU'),
            ('çÇ', 'cC'),
        ]:
            self.assertEqual(strip_accents(string),
                             string_without_accentuation)


if __name__ == '__main__':
    unittest.main()
