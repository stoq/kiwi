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

import gobject

def list_properties(gtype, parent=True):
    """
    Return a list of all properties for GType gtype, excluding
    properties in parent classes
    """
    pspecs = gobject.list_properties(gtype)
    if parent:
        return pspecs

    parent = gobject.type_parent(gtype)

    parent_pspecs = gobject.list_properties(parent)
    return [pspec for pspec in pspecs
                      if pspec not in parent_pspecs]

def type_register(gtype):
    """Register the type, but only if it's not already registered
    @param gtype: the class to register
    """

    # copied from gobjectmodule.c:_wrap_type_register
    if (getattr(gtype, '__gtype__', None) !=
        getattr(gtype.__base__, '__gtype__', None)):
        return False

    gobject.type_register(gtype)

    return True

def gsignal(name, *args, **kwargs):
    """
    Add a GObject signal to the current object.
    It current supports the following types:
        - str, int, float, long, object, enum
    @param name: name of the signal
    @type name: string
    @param args: types for signal parameters,
        if the first one is a string 'override', the signal will be
        overridden and must therefor exists in the parent GObject.
    @note: flags: A combination of;
      - gobject.SIGNAL_RUN_FIRST
      - gobject.SIGNAL_RUN_LAST
      - gobject.SIGNAL_RUN_CLEANUP
      - gobject.SIGNAL_NO_RECURSE
      - gobject.SIGNAL_DETAILED
      - gobject.SIGNAL_ACTION
      - gobject.SIGNAL_NO_HOOKS
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
            default_flags = gobject.SIGNAL_RUN_FIRST
        else:
            default_flags = gobject.SIGNAL_RUN_LAST

        flags = kwargs.get('flags', default_flags)
        if retval is not None and flags != gobject.SIGNAL_RUN_LAST:
            raise TypeError(
                "You cannot use a return value without setting flags to "
                "gobject.SIGNAL_RUN_LAST")

        dict[name] = (flags, retval, args)

def quote(msg):
    """
    Similar to urllib.quote but for glibs GMarkup
    @param msg: string to quote
    @returns: quoted string
    """
    msg = msg.replace('&', '&amp;')
    msg = msg.replace('<', '&lt;')
    msg = msg.replace('>', '&gt;')
    return msg
