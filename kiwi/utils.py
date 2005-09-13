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

import struct
import sys

import gobject

from kiwi.python import ClassInittableObject

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
            

class PropertyObject(ClassInittableObject):
    """
    I am an object which maps GObject properties to attributes
    To be able to use me, you must also subclass a gobject.
    """
    _default_values = {}
    def __init__(self, **kwargs):
        self._attributes = {}

        if not isinstance(self, gobject.GObject):
            raise TypeError("%r must be a GObject subclass" % self)

        defaults = self._default_values.copy()
        for kwarg in kwargs:
            if not kwarg in defaults:
                raise TypeError("Unknown keyword argument: %s" % kwarg)
        defaults.update(kwargs)
        for name, value in defaults.items():
            self._set(name, value)

    def __class_init__(cls, namespace):
        # Do not try to register gobject subclasses
        # If you try to instantiate an object you'll get a warning,
        # So it is safe to ignore here.
        if not issubclass(cls, gobject.GObject):
            return

        # The default value for enum GParamSpecs (returned by list_properties)
        # lacks the enum wrapper so save a reference to the value, it needs to
        # be done here because when we register the GType pygtk removes the
        # attribute __gproperties__. It's fixed in PyGTK CVS, so it can be
        # remove when we can depend on PyGTK 2.8
        pytypes = {}
        for prop_name, value in namespace.get('__gproperties__', {}).items():
            if gobject.type_is_a(value[0], gobject.GEnum):
                prop_name = prop_name.replace('-', '_')
                pytypes[prop_name] = value[3]

        # Register the type, here so don't have to do it explicitly, it
        # can be removed in PyGTK 2.8, since it does this magic for us.
        gobject.type_register(cls)

        # Create python properties for gobject properties, store all
        # the values in self._attributes, so do_set/get_property
        # can access them. Using set property for attribute assignments
        # allows us to add hooks (notify::attribute) when they change.
        default_values = {}
        for pspec in list_properties(cls, parent=False):
            prop_name = pspec.name.replace('-', '_')

            p = property(lambda self, n=prop_name: self._attributes[n],
                         lambda self, v, n=prop_name: self.set_property(n, v))
            setattr(cls, prop_name, p)

            # Resolve an integer to a real enum
            default_value = pspec.default_value
            if gobject.type_is_a(pspec.value_type, gobject.GEnum):
                pyenum = pytypes[prop_name]
                default_value = pyenum.__enum_values__[default_value]
                
            default_values[prop_name] = default_value

        cls._default_values.update(default_values)
        
    __class_init__ = classmethod(__class_init__)
        
    def _set(self, name, value):
        func = getattr(self, 'prop_set_%s' % name, None)
        if callable(func) and func:
            value = func(value)
        self._attributes[name] = value

    def get_attribute_names(self):
        return self._attributes.keys()

    def is_default_value(self, attr, value):
        return self._default_values[attr] == value
    
    def do_set_property(self, pspec, value):
        prop_name = pspec.name.replace('-', '_')
        self._set(prop_name, value)
        
    def do_get_property(self, pspec):
        prop_name = pspec.name.replace('-', '_')
        return self._attributes[prop_name]
    
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

def _max(c):
   return (1 << (8 * struct.calcsize(c)-1))-1

_MAX_INT = int(_max('i'))
_MAX_FLOAT = float(_max('f'))
_MAX_LONG = long(_max('l'))

def gproperty(name, type, *args, **kwargs):
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
        
    nick = kwargs.get('nick', name)
    blurb = kwargs.get('blurb', '')
    args = [type, nick, blurb]

    if type == str:
        args.append(kwargs.get('default', ''))
    elif type == int:
        args.append(kwargs.get('minimum', 0))
        args.append(kwargs.get('maximum', _MAX_INT))
        args.append(kwargs.get('default', 0))
    elif type == float:
        args.append(kwargs.get('minimum', 0.0))
        args.append(kwargs.get('maximum', _MAX_FLOAT))
        args.append(kwargs.get('default', 0.0))
    elif type == long:
        args.append(kwargs.get('minimum', 0L))
        args.append(kwargs.get('maximum', _MAX_LONG))
        args.append(kwargs.get('default', 0L))
    elif type == bool:
        args.append(kwargs.get('default', True))
    elif gobject.type_is_a(type, gobject.GEnum):
        default = kwargs.get('default')
        if default is None:
            raise TypeError("enum properties needs a default value")
        elif not isinstance(default, type):
            raise TypeError("enum value %s must be an instance of %r" %
                            (default, type))
        args.append(default)
    elif type == object:
        pass

    args.append(kwargs.get('flags', gobject.PARAM_READWRITE))

    if not '__gproperties__' in locals:
        dict = locals['__gproperties__'] = {}
    else:
        dict = locals['__gproperties__']

    dict[name] = tuple(args)

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
    
    return xrange(*slice.indices(limit))
