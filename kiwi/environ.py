#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""Environment helpers: path mangling and resource management"""

import commands
import errno
import gettext
import imp
import locale
import logging
import os
import platform
import sys

import pkg_resources

__all__ = ['Library', 'environ']

log = logging.getLogger('environ')

EnvironmentError = EnvironmentError


# From http://tinyurl.com/77ukj
def _is_frozen():
    "Helper function to check if we're frozen in a py2exe'd file"
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers")  # old py2exe
            or imp.is_frozen("__main__"))  # tools/freeze


class _KiwiProvider(pkg_resources.DefaultProvider):
    _my_resources = {}

    def __init__(self, module):
        pkg_resources.DefaultProvider.__init__(self, module)

        if module.__name__ in self._my_resources:
            self.module_path = self._my_resources[module.__name__]

    @classmethod
    def add_resource(cls, name, path=None):
        cls._my_resources[name] = path


pkg_resources.register_loader_type(type(None), _KiwiProvider)


class Environment:
    """Environment control

    When you want to access a resource on the filesystem, such as
    an image or a glade file you use this object.

    External libraries or applications are free to add extra directories"""

    def __init__(self, root='.'):
        self._root = root

    #
    #  Public
    #

    def get_root(self):
        return self._root

    def get_resource_string(self, domain, *resource):
        resource = '/'.join(resource)
        return pkg_resources.resource_string(domain, resource)

    def get_resource_filename(self, domain, *resource):
        resource = '/'.join(resource)
        return pkg_resources.resource_filename(domain, resource)

    def get_resource_exists(self, domain, *resource):
        resource = '/'.join(resource)
        return pkg_resources.resource_exists(domain, resource)

    def get_resource_names(self, domain, *resource):
        resource = '/'.join(resource)
        return pkg_resources.resource_listdir(domain, resource)


class Library(Environment):
    """A Library is a local environment object, it's a subclass of the
    Environment class.
    It's used by libraries and applications (through the Application class)

    It provides a way to manage local resources, which should only be seen
    in the current context.

    Libraries are usually instantiated in __init__.py in the topmost package
    in your library, an example usage is kiwi itself which does:

    >>> from kiwi.environ import Library
    >>> lib = Library('kiwi')
    >>> if lib.uninstalled:
    ...     lib.add_global_resource('glade', 'glade')
    ...     lib.add_global_resource('pixmap', 'pixmaps')

    which is combined with the following class in setup.py:

    >>> from kiwi.dist import KiwiInstallLib, setup, listfiles
    >>> class InstallLib(KiwiInstallLib):
    ...     name = 'kiwi'
    ...     global_resources = dict(glade='$datadir/glade',
    ...                             pixmap='$datadir/pixmaps')
    >>> setup(data_files=[
    ...           ('share/kiwi/glade', listfiles('glade', '*.glade')),
    ...           ('share/kiwi/pixmaps', listfiles('pixmaps', '*.png'))],
    ...       cmdclass=dict(install_lib=InstallLib))

    It may seems like a bit of work, but this is everything that's needed
    for kiwi to figure out how to load resources when installed and when
    running in an uninstalled mode, eg directly from the source tree.
    To locate a pixmap called kiwi.png the following is enough:

    >>> from kiwi.environ import environ
    >>> environ.find_resource('pixmap', 'kiwi.png')
    '/usr/share/kiwi/pixmaps/kiwi.png' # installed mode

    Which will lookup the resource kiwi.png in the domain pixmap, which
    points to $datadir/pixmaps (eg $prefix/share/kiwi/pixmaps) when running
    in installed mode and from $builddir/pixmaps otherwise.

    """

    def __init__(self, name, root='..', dirname=None):
        """
        Creates a new library, this is usually called in __init__.py in a
        toplevel package. All resources will be relative to the I{root}
        directory.

        :param name: name of the library
        :param root: root directory
        :param dirname:
        """
        self.name = name

        # py2exe
        if _is_frozen():
            log.info('py2exe found')
            executable = os.path.realpath(os.path.abspath(sys.executable))
            root = os.path.dirname(executable)
        # normal
        else:
            if dirname is None:
                # Figure out the absolute path to the caller
                caller = sys._getframe(1).f_locals['__file__']
                dirname = os.path.split(caller)[0]

            dirname = os.path.realpath(os.path.abspath(dirname))
            root = os.path.abspath(os.path.join(dirname, root))

        Environment.__init__(self, root=root)

        basedir = os.path.join(root, 'lib', 'python%d.%d' %
                               sys.version_info[:2], 'site-packages')
        if os.path.exists(basedir):
            sys.path.insert(0, basedir)
        g = globals()
        l = locals()
        try:
            module = __import__(name, g, l)
        except ImportError:
            raise ImportError("Failed to import module %s" % name)

        # Load installed
        try:
            module = __import__(name + '.__installed__', g, l, [name])
        except ImportError:
            self.prefix = sys.prefix
            uninstalled = True
            # FIXME: This is to support our development schema where data
            # is on the source's toplevel dir inside 'data'
            resource_path = os.path.join(root, 'data')
            bdist_type = ''
        else:
            self.prefix = module.prefix
            uninstalled = False
            prefix = module.prefix or sys.prefix
            resource_path = os.path.join(prefix, module.datadir)
            bdist_type = getattr(module, 'bdist_type', '')

        self.bdist_type = bdist_type
        self.uninstalled = uninstalled
        self.module = module

        _KiwiProvider.add_resource(name, path=resource_path)

    #
    #  Private
    #

    def _check_translation(self, domain, directory):
        loc = locale.getlocale()[0]

        # We're not interested in warnings for these locales
        if loc in (None, 'C', 'en_US', 'English_United States'):
            return

        # check sv_SE and sv
        locales = [loc]
        if '_' in loc:
            locales.append(loc.split('_')[0])

        for l in locales:
            path = os.path.join(directory, l, 'LC_MESSAGES', domain + '.mo')
            if os.path.exists(path):
                break
        else:
            log.warn('No %s translation found for domain %s' % (loc, domain))

    #
    #  Public
    #

    def enable_translation(self, domain=None, enable_global=False):
        """
        Enables translation for a library

        :param domain: optional, if not specified name sent to constructor
          will be used
        :param enable_global: if we should set that domain as the
          default domain when using gettext without one
        """
        if not domain:
            domain = self.name

        if (not self.uninstalled and
                pkg_resources.resource_exists(domain, 'locale')):
            localedir = pkg_resources.resource_filename(domain, 'locale')
        elif not self.uninstalled:
            localedir = None
        else:
            localedir = os.path.join(self.get_root(), 'locale')

        directory = gettext.bindtextdomain(domain, localedir)
        self._check_translation(domain, directory)
        # For libglade, but only on non-win32 systems
        if hasattr(locale, 'bindtextdomain'):
            locale.bindtextdomain(domain, localedir)

        # Gtk+ only supports utf-8, it makes no sense to support
        # other encodings in kiwi it self
        # This is not present in Python 2.3
        if hasattr(gettext, 'bind_textdomain_codeset'):
            gettext.bind_textdomain_codeset(domain, 'utf-8')

        if enable_global:
            gettext.textdomain(domain)
            # For libglade, but only on non-win32 systems
            if hasattr(locale, 'textdomain'):
                locale.textdomain(domain)

        if platform.system() == 'Windows':
            from ctypes import cdll
            libintl = cdll.intl
            libintl.bindtextdomain(domain, localedir)
            libintl.bind_textdomain_codeset(domain, 'UTF-8')
            if enable_global:
                libintl.textdomain(domain)
            del libintl

    def get_revision(self):
        """Get the current VCS revision"""
        if self.uninstalled:
            status, output = commands.getstatusoutput('git rev-parse --short HEAD')
            if status == 0:
                return output
            revision = os.path.join(
                self._root, '.bzr', 'branch', 'last-revision')
            try:
                fp = open(revision)
            except IOError, e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                return fp.read().split()[0]
        else:
            return str(self.module.revision)


# Global variables
environ = Environment()
