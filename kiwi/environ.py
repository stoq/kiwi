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
        
    def _add_resource_variable(self, resource, variable):
        """Add resources from an environment variable"""
        env = os.environ.get(variable, '')
        for path in env.split(':'):
            if not path:
                continue
            self.add_resource(resource, env)
            
    def add_resource(self, resource, path):
        if not os.path.isdir(path):
            raise EnvironmentError("path %s must be a directory" % path)

        path = os.path.join(self._root, path)
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
        
        if not resource in self._resources:
            raise EnvironmentError("No resource called: %s" % resource)

        for path in self._resources[resource]:
            filename = os.path.join(self._root, path, name)
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
    def __init__(self, name, root='..'):
        self.name = name
        # Figure out the absolute path to the caller
        caller = sys._getframe(1).f_locals['__file__']
        caller_abs = os.path.split(caller)[0]
        root = os.path.abspath(os.path.join(caller_abs, root))

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
                raise ValueError("module %s.__installed must define a "
                                 "resources attribute" % name)
            if not hasattr(module, 'global_resources'):
                raise ValueError("module %s.__installed must define a "
                                 "global_resources attribute" % name)
            self.add_resources(**module.resources)
            self.add_global_resources(**module.global_resources)

        self.uninstalled = uninstalled
        
    def enable_translation(self, domain=None, locale='locale',
                           charset='utf-8'):
        if not domain:
            domain = self.name
            
        self._resources.get(locale)
        gettext.bindtextdomain(domain, locale)
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
        Library.__init__(self, name, root)
        self._path = path

    def _get_main(self):
        path = self._path
        main_module = os.path.join(self.root, path)

        try:
            module = __import__(main_module, globals(), locals(), path)
        except Exception, e:
            raise SystemExit("ERROR: Failed to import required module %s\n\n"
                             "Exception raised during import:\n %s: %s\n" %
                             (main_module, e.__class__.__name__, e))

        main = getattr(module, path, None)
        if not main or not callable(main):
            raise SystemExit("ERROR: Could not find item '%s' in module %s" %
                             path, main_module)
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
