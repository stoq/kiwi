import fnmatch
import inspect
import os
import sys
import time

import gtk
try:
    import pygtk
    pygtk.require('2.0')
except:
    pass
from zope.interface import implementedBy, interface

import kiwi
from kiwi.python import ClassInittableObject, namedAny


def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)

dir = os.path.dirname(__file__)
if not dir in sys.path:
    sys.path.insert(0, os.path.join(dir))


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


def _get_kiwi_sources(root, with_toplevel_sources=True):
    for dirpath in ['kiwi', 'tests']:
        path = os.path.join(root, dirpath)
        for fname in _list_recursively(path, '*.py'):
            if fname.endswith('__init__.py'):
                continue
            if fname.endswith('run_all_tests.py'):
                # Sourcing this will make tests run again and again
                continue

            yield fname

        if with_toplevel_sources:
            for module in ['setup', 'kiwiwidgets']:
                yield os.path.join(root, module + '.py')


def _get_all_classes(root):
    root = os.path.dirname(os.path.dirname(kiwi.__file__)) + '/'
    # We cannot import setup.py neither kiwiwidgets.py using namedAny
    for filename in _get_kiwi_sources(root, with_toplevel_sources=False):
        # Avoid tests.
        if 'test/' in filename:
            continue

        modulename = filename[len(root):-3].replace(os.path.sep, '.')
        try:
            module = namedAny(modulename)
        except ImportError as e:
            # FIXME: Some modules (like db.sqlobj, db.sqlalch) will try to
            # import things that we don't have on out development environment
            print ("module %s is trying to import something "
                   "not importable: %s" % (modulename, e))
            continue

        for unused, klass in inspect.getmembers(module, inspect.isclass):
            yield klass


def get_interfaces_for_package(package):
    for klass in _get_all_classes(package):
        if not implementedBy(klass):
            continue
        if not klass.__module__.startswith(package + '.'):
            continue
        if issubclass(klass, interface.InterfaceClass):
            continue
        yield klass


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
