#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
# Author(s): Christian Reis <kiko@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#         

import gettext
import os
import sys

__all__ = ['Application', 'Library', 'environ', 'require_gazpacho',
           'is_gazpacho_required']

# copied from twisted/python/reflect.py
def namedAny(name):
    """Get a fully named package, module, module-global object, or attribute.
    """
    names = name.split('.')
    topLevelPackage = None
    moduleNames = names[:]
    while not topLevelPackage:
        try:
            trialname = '.'.join(moduleNames)
            topLevelPackage = __import__(trialname)
        except ImportError:
            # if the ImportError happened in the module being imported,
            # this is a failure that should be handed to our caller.
            # count stack frames to tell the difference.
            import traceback
            exc_info = sys.exc_info()
            if len(traceback.extract_tb(exc_info[2])) > 1:
                try:
                    # Clean up garbage left in sys.modules.
                    del sys.modules[trialname]
                except KeyError:
                    # Python 2.4 has fixed this.  Yay!
                    pass
                raise exc_info[0], exc_info[1], exc_info[2]
            moduleNames.pop()
    
    obj = topLevelPackage
    for n in names[1:]:
        obj = getattr(obj, n)
        
    return obj

class Environment:
    """Environment control

    When you want to access a resource on the filesystem, such as
    an image or a glade file you use this object.

    External libraries or applications are free to add extra directories"""

    def __init__(self, root='.'):
        self._resources = {}
        self._root = root
        
        self._add_resource_variable("glade", "KIWI_GLADE_PATH")
        self._add_resource_variable("image", "KIWI_IMAGE_PATH")

    def get_root(self):
        return self._root
    
    def _add_resource_variable(self, resource, variable):
        """Add resources from an environment variable"""
        env = os.environ.get(variable, '')
        for path in env.split(':'):
            if not path:
                continue
            self.add_resource(resource, env)

    def get_resource_paths(self, resource):
        if not resource in self._resources:
            raise EnvironmentError("No resource called: %s" % resource)
        return self._resources[resource]
            
    def add_resource(self, resource, path):
        path = os.path.join(self._root, path)
        if not os.path.isdir(path):
            raise EnvironmentError("path %s must be a directory" % path)

        resources = self._resources
        if not resource in resources:
            resources[resource] = [path]
        else:
            resources[resource].append(path)

    def add_resources(self, **kwargs):
        for resource, path in kwargs.items():
            self.add_resource(resource, path)
            
    def find_resource(self, resource, name):
        """Locate a specific resource of called name of type resource"""

        resource_paths = self.get_resource_paths(resource)
        for path in resource_paths:
            filename = os.path.join(self._root, path, name)
            if os.path.exists(filename):
                return filename

        # Finally try to load the file from the current directory
        filename = os.path.join(self._root, name)
        if os.path.exists(filename):
            return filename
        
        raise EnvironmentError("Could not find %s resource: %s" % (
            resource, name))

class Library(Environment):
    """A Library is a local environment object, it's a subclass of the
    Environment class.
    It's used by libraries and applications (through the Application class)
    
    It provides a way to manage local resources, which should only be seen
    in the current context.
    """
    def __init__(self, name, root='..', dirname=None):
        self.name = name
        if dirname == None:
            # Figure out the absolute path to the caller
            caller = sys._getframe(1).f_locals['__file__']
            dirname = os.path.split(caller)[0]
            
        dirname = os.path.realpath(os.path.abspath(dirname))
        root = os.path.abspath(os.path.join(dirname, root))
        Environment.__init__(self, root=root)
        
        # Load installed
        try:
            module = __import__(name + '.__installed__',
                                globals(), locals(), name)
        except ImportError, e:
            uninstalled = True
        else:
            uninstalled = False
            if not hasattr(module, 'resources'):
                raise ValueError("module %s.__installed__ must define a "
                                 "resources attribute" % name)
            if not hasattr(module, 'global_resources'):
                raise ValueError("module %s.__installed__ must define a "
                                 "global_resources attribute" % name)
            self.add_resources(**module.resources)
            self.add_global_resources(**module.global_resources)

        self.uninstalled = uninstalled

    def enable_translation(self, domain=None, locale='locale',
                           charset='utf-8'):
        if not domain:
            domain = self.name

        # XXX: locale should not be a list
        localedir = self._resources.get(locale)
        if localedir:
            gettext.bindtextdomain(domain, localedir[0])
        gettext.bind_textdomain_codeset(domain, charset)

    def add_global_resource(self, resource, path):
        """Convenience method to add a global resource.
        This is the same as calling kiwi.environ.environ.add_resource
        """
        global environ
        environ.add_resource(resource, os.path.join(self._root, path))

    def add_global_resources(self, **kwargs):
        for resource, path in kwargs.items():
            self.add_global_resource(resource, path)

class Application(Library):
    """An Application extends a library. The additions are:
    - a run() method, used to run the application
    - path, a reference to the callable object to run, defaults to 'main'
    """
    def __init__(self, name, root='..', path='main'):
        dirname = os.path.abspath(os.path.dirname(sys.argv[0]))
        Library.__init__(self, name, root, dirname)
        self._path = path

    def _get_main(self):
        try:
            module = namedAny(self._path)
        except (ValueError, AttributeError, ImportError), e:
            raise SystemExit("ERROR: Could not find item '%s', %s" %
                             (self._path, e))
            
        main = getattr(module, 'main', None)
        if not main or not callable(main):
            raise SystemExit("ERROR: Could not find item '%s' in module %s" %
                             'main', self._path)
        return main

    def enable_translation(self, domain=None, locale='locale',
                           charset='utf-8'):
        if not domain:
            domain = self.name
            
        Library.enable_translation(self, domain, locale, charset)
        gettext.textdomain(domain)
        
    def run(self):
        main = self._get_main()
        
        try:
            sys.exit(main(sys.argv))
        except KeyboardInterrupt:
            raise SystemExit

_require_gazpacho_loader = False

def require_gazpacho():
    global _require_gazpacho_loader
    _require_gazpacho_loader = True

def is_gazpacho_required():
    global _require_gazpacho_loader
    return _require_gazpacho_loader

# Global instance, shared between apps and libraries
environ = Environment()
