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

import os

__all__ = ['environ']

class KiwiEnvironment:
    """Environment control

    When you want to access a resource on the filesystem, such as
    an image or a glade file you use this object.

    External libraries or applications are free to add extra directories"""

    def __init__(self):
        self._resources = {}

    def add_resource(self, resource, path):
        if not resource in self._resources:
            paths = self._resources[resource] = []
        else:
            paths = self._resources[resource]

        paths.append(path)
        
    def add_resource_variable(self, resource, variable):
        """Add resources from an environment variable"""
        env = os.environ.get(variable, '')
        for path in env.split(':'):
            self.add_resource(resource, env)
            
    def find_resource(self, resource, name):
        """Locate a specific resource of called name of type resource"""
        
        if not resource in self._resources:
            raise EnvironmentError("No resource called: %s" % resource)

        for path in self._resources[resource]:
            filename = os.path.join(path, name)
            if os.path.exists(filename):
                return filename

        raise EnvironmentError("Could not find %s resource: %s" % (
            resource, name))
                               
environ = KiwiEnvironment()
environ.add_resource_variable("glade", "KIWI_GLADE_PATH")
environ.add_resource_variable("image", "KIWI_IMAGE_PATH")

_require_gazpacho_loader = False

def require_gazpacho():
    global _require_gazpacho_loader
    _require_gazpacho_loader = True

def is_gazpacho_required():
    global _require_gazpacho_loader
    return _require_gazpacho_loader
