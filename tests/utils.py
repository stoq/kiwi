import fnmatch
import os
import sys
import time

try:
    import pygtk
    pygtk.require('2.0')
except:
    pass

import gtk


def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)

dir = os.path.dirname(__file__)
if not dir in sys.path:
    sys.path.insert(0, os.path.join(dir))

from kiwi.environ import environ
environ.add_resource('glade', dir)

from kiwi.python import ClassInittableObject

import kiwi


def _list_recursively(directory, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, pattern):
            # skip backup files
            if (filename.startswith('.#') or
                filename.endswith('~')):
                continue
            matches.append(os.path.join(root, filename))

    return matches


def _get_kiwi_sources(root):
    for dirpath in ['kiwi', 'tests']:
        path = os.path.join(root, dirpath)
        for fname in _list_recursively(path, '*.py'):
            if fname.endswith('__init__.py'):
                continue
            yield fname

        for module in ['setup', 'kiwiwidgets']:
            yield os.path.join(root, module + '.py')


class SourceTest(ClassInittableObject):
    @classmethod
    def __class_init__(cls, namespace):
        root = os.path.dirname(os.path.dirname(kiwi.__file__)) + '/'
        cls.root = root
        for filename in _get_kiwi_sources(root):
            testname = filename[len(root):]

            if not cls.filename_filter(testname):
                continue

            testname = testname[:-3].replace('/', '_')
            name = 'test_%s' % (testname, )
            func = lambda s, r=root, f=filename: s.check_filename(r, f)
            func.__name__ = name
            setattr(cls, name, func)

    @classmethod
    def filename_filter(cls, filename):
        if cls.__name__ == 'SourceTest':
            return False
        else:
            return True

    def check_filename(self, root, filename):
        pass
