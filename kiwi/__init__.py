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

"""Kiwi is a library designed to make developing graphical applications as
easy as possible. It offers both a framework and a set of enhanced widgets,
and is based on Python and GTK+. Kiwi borrows concepts from MVC, Java Swing
and Microsoft MFC, but implements a set of unique classes that take
advantage of the flexibility and simplicity of Python to make real-world
application creation much easier.

Kiwi includes a Framework and a set of enhanced widgets

    - Authors:
      - Christian Reis <kiko@async.com.br>
      - Johan Dahlin <jdahlin@async.com.br>
    - Website: U{http://www.async.com.br/projects/kiwi/}
    - Organization: Async Open Source
"""

import sys

try:
    import gobject
    gobject
except ImportError:
    raise SystemExit(
        "PyGTK 2.8 or PyGObject 2.9.0 or higher is required by kiwi")

from kiwi.__version__ import version as kiwi_version
from kiwi.environ import Library

assert kiwi_version # pyflakes

lib = Library('kiwi')
if lib.uninstalled:
    lib.add_resource('locale', 'locale')
    lib.add_global_resource('glade', 'glade')
    lib.add_global_resource('pixmap', 'pixmaps')
lib.enable_translation()

del Library, lib

class ValueUnset:
    """To differentiate from places where None is a valid default. Used
    mainly in the Kiwi Proxy"""
    pass

def _warn(msg):
    sys.stderr.write("Kiwi warning: "+msg+"\n")

__all__ = ['ValueUnset', '_warn', 'kiwi_version']

