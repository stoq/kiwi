#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
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

import sys

import gobject

def gsignal(name, *args, **kwargs):
    """
    Add a GObject signal to the current object.
    @type name:   string
    @type args:   types
    @type kwargs: keyword argument 'flags' and/or 'retval'
    """

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
    finally:
        del frame
        
    if not '__gsignals__' in locals:
        dict = locals['__gsignals__'] = {}
    else:
        dict = locals['__gsignals__']

    if args and args[0] == 'override':
        dict[name] = 'override'
    else:
        flags = kwargs.get('flags', gobject.SIGNAL_RUN_FIRST)
        retval = kwargs.get('retval', None)
    
        dict[name] = (flags, retval, args)

def gproperty(name, type, default=None, nick=None,
              flags=gobject.PARAM_READWRITE):
    """
    Add a GObject property to the current object.
    @type type:    type
    @type default: default value
    @type name:    string
    @type nick:    string
    @type flags:   a gobject.ParamFlag
    """

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
    finally:
        del frame
        
    if not '__gproperties__' in locals:
        dict = locals['__gproperties__'] = {}
    else:
        dict = locals['__gproperties__']

    if nick is None:
        nick = name

    if default is None:
        if type == str:
            default = ''
        elif type == int:
            default = 0
        elif type == float:
            default = 0.0
        elif type == bool:
            default = True
            
    dict[name] = (type, name, nick, default, flags)

def clamp(x, low, high):
    """
    Ensures that x is between the limits set by low and high.
    For example,
    * clamp(5, 10, 15) is 10.
    * clamp(15, 5, 10) is 10.
    * clamp(20, 15, 25) is 20. 

    @param    x: the value to clamp.
    @param  low: the minimum value allowed.
    @param high: the maximum value allowed.
    """
    
    return min(max(x, low), high)

def slicerange(slice, limit):
    """Takes a slice object and returns a range iterator

    @param slice: slice object
    @param limit: maximum value allowed"""

    args = []

    # readonly, we need to copy them
    start, stop, step = slice.start, slice.stop, slice.step

    # start is only set if [n:m]
    if start != None:
        if start < 0:
            # [-n:m]
            start += limit
        args.append(start)
        
    # stop is always set
    if stop < 0:
        # [n:-m]
        stop += limit
        
    # [:] -> [0:maxint], so cut at limit
    args.append(min(stop, limit))

    # step is only set if [n:m:o]
    if slice.step != None:
        args.append(step)

    return xrange(*args)
