#!/usr/bin/env python
import os
import glob
import sys
import inspect
import unittest

myself = os.path.abspath(__file__)
testdir =  os.path.dirname(myself)
if testdir not in sys.path:
    sys.path.append(testdir)
sys.path.insert(0, os.path.join(testdir, '..'))

print 'Running tests on', testdir

suite = unittest.TestSuite()

for file in glob.glob(os.path.join(testdir, 'test_*.py')):
    filename = os.path.basename(file)
    modulename = os.path.splitext(filename)[0]
    mod = __import__(modulename, globals(), locals())
    members = [mem[1] for mem in inspect.getmembers(mod, inspect.isclass) \
               if issubclass(mem[1], unittest.TestCase) \
               and not mem[1] == unittest.TestCase]
    for mem in members:
        suite.addTest(unittest.makeSuite(mem))


unittest.TextTestRunner(verbosity=2).run(suite)
