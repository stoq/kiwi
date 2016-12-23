#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2007 Async Open Source
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
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""GObject utilities and addons"""

import sys

try:
    from gi.repository import GObject
    GObject  # pyflakes
except ImportError:
    raise SystemExit("python-gobject is required by kiwi.utils")


# FIXME gtk3: Is this still necessary?
# Monkey patch gobject to support enum properties
gprop = GObject.Property
parent_type_from_parent = gprop._type_from_python
parent_get_pspec_args = gprop.get_pspec_args


def _type_from_python(self, type_):
    if issubclass(type_, GObject.GEnum):
        return type_.__gtype__
    else:
        return parent_type_from_parent(self, type_)

gprop._type_from_python = _type_from_python


def _get_pspec_args(self):
    if GObject.type_is_a(self.type, GObject.GEnum):
        return (self.type, self.nick, self.blurb, self.default, self.flags)
    else:
        return parent_get_pspec_args(self)

gprop.get_pspec_args = _get_pspec_args


def list_properties(gtype, parent=True):
    """
    Return a list of all properties for GType gtype, excluding
    properties in parent classes
    """
    pspecs = GObject.list_properties(gtype)
    if parent:
        return pspecs

    parent = GObject.type_parent(gtype)

    parent_pspecs = GObject.list_properties(parent)
    return [pspec for pspec in pspecs
            if pspec not in parent_pspecs]


def type_register(gtype):
    """Register the type, but only if it's not already registered
    :param gtype: the class to register
    """

    # copied from gobjectmodule.c:_wrap_type_register
    if (getattr(gtype, '__gtype__', None) !=
        getattr(gtype.__base__, '__gtype__', None)):
        return False

    GObject.type_register(gtype)

    return True


def gsignal(name, *args, **kwargs):
    """
    Add a GObject signal to the current object.
    It current supports the following types:
        - str, int, float, long, object, enum
    :param name: name of the signal
    :type name: string
    :param args: types for signal parameters,
        if the first one is a string 'override', the signal will be
        overridden and must therefor exists in the parent GObject.
    @note: flags: A combination of;
      - GObject.SignalFlags.RUN_FIRST
      - GObject.SignalFlags.RUN_LAST
      - GObject.SignalFlags.RUN_CLEANUP
      - GObject.SignalFlags.NO_RECURSE
      - GObject.SignalFlags.DETAILED
      - GObject.SignalFlags.ACTION
      - GObject.SignalFlags.NO_HOOKS
    @note: retval: return value in signal callback
    """

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
    finally:
        del frame

    dict = locals.setdefault('__gsignals__', {})

    if args and args[0] == 'override':
        dict[name] = 'override'
    else:
        retval = kwargs.get('retval', None)
        if retval is None:
            default_flags = GObject.SignalFlags.RUN_FIRST
        else:
            default_flags = GObject.SignalFlags.RUN_LAST

        flags = kwargs.get('flags', default_flags)
        if retval is not None and flags != GObject.SignalFlags.RUN_LAST:
            raise TypeError(
                "You cannot use a return value without setting flags to "
                "GObject.SignalFlags.RUN_LAST")

        dict[name] = (flags, retval, args)


def pango_pixels(value):
    """Convert pango units to pixels.

    Based on the *PANGO_PIXELS* macro:
    http://developer.gnome.org/pango/stable/pango-Glyph-Storage.html#PANGO-PIXELS:CAPS
    """
    return (value + 512) >> 10
