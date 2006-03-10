#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006 Async Open Source
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
#            Ali Afshar <aafshar@gmail.com>

class Interface(object):
    pass

class AlreadyImplementedError(Exception):
    """Called when a utility already exists."""

class _UtilityHandler(object):
    def __init__(self):
        self._utilities = {}

    def provide(self, iface, obj):
        global _interfaces
        if not issubclass(iface, _interfaces):
            raise TypeError(
                "iface must be an Interface subclass and not %r" % iface)

        if iface in self._utilities:
            raise AlreadyImplementedError("%s is already implemented" % iface)
        self._utilities[iface] = obj

    def get(self, iface):
        global _interfaces
        if not issubclass(iface, _interfaces):
            raise TypeError(
                "iface must be an Interface subclass and not %r" % iface)

        if not iface in self._utilities:
            raise NotImplementedError("No utility provided for %r" % iface)

        return self._utilities[iface]

def provide_utility(iface, utility):
    """
    Set the utility for the named interface. If the utility is already
    set, an {AlreadyImplementedError} is raised.

    @param iface: interface to set the utility for.
    @param utility: utility providing the interface.
    """
    global _handler
    _handler.provide(iface, utility)

def get_utility(iface):
    """
    Get the utility for the named interface. If the utility is not
    available (has not been set) a {NotImplementedError} is raised.

    @param iface: interface to retrieve the utility for.
    @type iface: utility providing the interface
    """

    global _handler
    return _handler.get(iface)

try:
    from zope.interface import Interface as ZInterface
    _interfaces = Interface, ZInterface
except ImportError:
    _interfaces = Interface

_handler = _UtilityHandler()
