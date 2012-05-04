import unittest

import pep8

from utils import SourceTest

ERRORS = [
    'E111', # indentation is not a multiple of four
    'E112', # expected an indented block
    'E113', # unexpected indentation
    'E201', # whitespace after '{'
    'E202', # whitespace before ')'
    'E203', # whitespace before ':'
    'E211', # whitespace before '('
    'E221', # multiple spaces before operator
    'E225', # missing whitespace around operator
    'E231', # E231 missing whitespace after ','/':'
    'E241', # multiple spaces after operator
    'E251', # no spaces around keyword / parameter equals
    'E262', # inline comment should start with '# '
    'W291', # trailing whitespace
    'W292', # no newline at end of file
    'W293', # blank line contains whitespace
    'E301', # expected 1 blank line, found 0
    'E302', # expected 2 blank lines, found 1
    'E303', # too many blank lines
    'W391', # blank line at end of file
    'E401', # multiple imports on one line
    'W601', # in instead of dict.has_key
    'W602', # deprecated form of raising exception
    'W603', # '<>' is deprecated, use '!='"
    'W604', # backticks are deprecated, use 'repr()'
    'E701', # multiple statements on one line (colon)
    'E702', # multiple statements on one line (semicolon)
    ]


class TestPEP8(SourceTest, unittest.TestCase):
    """Check for pep8 problems on kiwi sources"""

    def check_filename(self, root, filename):
        pep8.process_options([
            '--repeat',
            '--select=%s' % (','.join(ERRORS), ), filename
            ])
        pep8.input_file(filename)
        result = pep8.get_count()
        if result:
            raise AssertionError("ERROR: %d PEP8 errors in %s" % (result,
                                                                  filename))
