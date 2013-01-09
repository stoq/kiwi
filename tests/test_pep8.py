import os
import unittest
import subprocess
import sys

from utils import SourceTest

_IGNORED_ERRORS = [
    'E125',  # continuation line does not distinguish itself from next logical line
    'E501',  # line too long
]


class TestPEP8(SourceTest, unittest.TestCase):
    """Check for pep8 problems on kiwi sources"""

    def check_filename(self, root, filename):
        cmd = [sys.executable,
               os.path.join(root, 'tools', 'pep8.py'),
               '--count',
               '--repeat',
               '--ignore=%s' % (','.join(_IGNORED_ERRORS), ),
               filename]

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        result = p.returncode
        if result:
            raise AssertionError("ERROR: %d PEP8 errors in %s" %
                                 (result, stdout))
