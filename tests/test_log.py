import cStringIO
import logging
import os
import sys
import tempfile
import unittest

from kiwi.log import Logger, set_log_file

class LogTest(unittest.TestCase):
    def setUp(self):
        self.filename = tempfile.mktemp()
        self.log = Logger('log')

    def tearDown(self):
        if os.path.exists(self.filename):
            try:
                os.unlink(self.filename)
            except OSError: # win32 permission error
                pass

    def testSetLogFile(self):
        set_log_file(self.filename, 'log')
        self.log.info("sliff")
        lines = open(self.filename).readlines()
        self.assertEqual(len(lines), 1)
        self.failUnless('sliff' in lines[0])


    def testStdErr(self):
        root = logging.getLogger()
        stream = root.handlers[0]
        fd = cStringIO.StringIO()
        stream.stream = fd
        self.log.warning("this is a warning")
        stream.stream = sys.stderr
        fd.seek(0)
        lines = fd.readlines()
        self.assertEqual(len(lines), 1)
        self.failUnless('this is a warning' in lines[0])
