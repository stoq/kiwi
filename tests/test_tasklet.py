import unittest

import gobject

from kiwi.tasklet import WaitForSignal

import utils

class TestWaitForSignal(unittest.TestCase):
    def testBadArguments(self):
        self.assertRaises(TypeError, WaitForSignal, '', '')
        self.assertRaises(ValueError, WaitForSignal, gobject.GObject(), 'foo')

    def testGoodArgumnets(self):
        WaitForSignal(gobject.GObject(), 'notify')

if __name__ == '__main__':
    unittest.main()
