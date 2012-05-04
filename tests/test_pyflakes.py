import _ast
import compiler
import sys
import unittest

import pyflakes

from utils import SourceTest


class TestPyflakes(SourceTest, unittest.TestCase):
    """Check for pyflakes problems on kiwi sources"""

    def setUp(self):
        self.checker = __import__('pyflakes.checker').checker

    def check_filename(self, root, filename):
        warnings = []
        msgs = []
        result = 0
        try:
            fd = file(filename, 'U')
            try:
                result = self._check(fd.read(), filename, warnings)
            finally:
                fd.close()
        except IOError, msg:
            print >> sys.stderr, "%s: %s" % (filename, msg.args[1])
            result = 1

        warnings.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for warning in warnings:
            msg = str(warning).replace(root, '')
            print msg
            msgs.append(msg)
        if result:
            raise AssertionError("%d warnings:\n%s\n" % (len(msgs),
                                                         '\n'.join(msgs)))

    # stolen from pyflakes
    def _check(self, codeString, filename, warnings):
        try:
            if pyflakes.__version__ == '0.4.0':
                compile(codeString, filename, "exec")
                tree = compiler.parse(codeString)
            else:
                tree = compile(codeString,
                               filename, "exec", _ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError), value:
            msg = value.args[0]

            (lineno, offset, text) = value.lineno, value.offset, value.text

            # If there's an encoding problem with the file, the text is None.
            if text is None:
                # Avoid using msg, since for the only known case, it contains a
                # bogus message that claims the encoding the file declared was
                # unknown.
                print >> sys.stderr, "%s: problem decoding source" % (filename)
            else:
                line = text.splitlines()[-1]

                if offset is not None:
                    offset = offset - (len(text) - len(line))

                print >> sys.stderr, '%s:%d: %s' % (filename, lineno, msg)
                print >> sys.stderr, line

                if offset is not None:
                    print >> sys.stderr, " " * offset, "^"

            return 1
        except UnicodeError, msg:
            print >> sys.stderr, 'encoding error at %r: %s' % (filename, msg)
            return 1
        else:
            # Okay, it's syntactically valid.  Now parse it into an ast
            # and check it.
            w = self.checker.Checker(tree, filename)
            warnings.extend(w.messages)
            return len(warnings)
