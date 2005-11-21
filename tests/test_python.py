import unittest

from kiwi.python import slicerange

class SliceTest(unittest.TestCase):
    def genlist(self, limit, start, stop=None, step=None):
        if stop == None:
            stop = start
            start = None
            
        return list(slicerange(slice(start, stop, step), limit))
    
    def testStop(self):
        self.assertEqual(self.genlist(10, 10), range(10))
        self.assertEqual(self.genlist(10, -5), range(5))
        self.assertEqual(self.genlist(10, -15), [])
        self.assertEqual(self.genlist(5, 10), range(5))
        self.assertEqual(self.genlist(0, 10), [])

    def testStartStop(self):
        self.assertEqual(self.genlist(10, 0, 10), range(10))
        self.assertEqual(self.genlist(10, 1, 9), range(10)[1:9])
        self.assertEqual(self.genlist(10, -1, -1), range(10)[-1:-1])
        self.assertEqual(self.genlist(10, 0, -15), range(10)[0:-15])
        self.assertEqual(self.genlist(10, 15, 0), range(10)[-15:0])
        
    def testStartStopStep(self):
        self.assertEqual(self.genlist(10, 0, 10, 2), range(10)[0:10:2])
