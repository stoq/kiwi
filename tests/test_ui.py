import os
import subprocess
import sys
import unittest

testdir = os.path.dirname(__file__)
rootdir = os.path.dirname(testdir)


class TestUI(unittest.TestCase):
    def setUp(self):
        self._dir = os.getcwd()
        os.chdir(rootdir)

    def tearDown(self):
        os.chdir(self._dir)

    def _test_filename(self, filename):
        cmd = '%s %s -v %s' % (sys.executable,
                               os.path.join(rootdir, 'bin', 'kiwi-ui-test'),
                               os.path.join('tests', 'ui', filename))
        proc = subprocess.Popen(cmd, shell=True)
        status = proc.wait()

        if status != 0:
            raise AssertionError("UI Test %s failed" % filename)


# Disable UI tests on win32, they do not quite work yet.
if sys.platform != 'win32':
    uidir = os.path.join(testdir, 'ui')
    for filename in os.listdir(uidir):
        if not filename.endswith('.doctest'):
            continue
        name = 'test_' + filename[:-7]

        func = lambda s, filename=filename: TestUI._test_filename(s, filename)
        func.__name__ = name
        setattr(TestUI, name, func)
        del func
