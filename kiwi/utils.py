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
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""GObject utilities and addons"""

import os
import struct
import sys

import gobject

HAVE_2_6 = gobject.pygtk_version[:2] == (2, 6)

# When we can depend on 2.8 clean this up, so ClassInittable does not
# need to be tied to GObjectMeta, since it doesn't need to be a GObject
# Always use type for epydoc, since GObjectMeta creates lots of trouble
# for us when using fake objects.
if HAVE_2_6 or os.path.basename(sys.argv[0]) == 'epyrun':
    metabase = type
else:
    metabase = gobject.GObjectMeta

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

class _GObjectClassInittableMetaType(metabase):
    def __init__(self, name, bases, namespace):
        metabase.__init__(self, name, bases, namespace)
        self.__class_init__(namespace)

class _GobjectClassInittableObject(object):
    __metaclass__ = _GObjectClassInittableMetaType

    def __class_init__(cls, namespace):
        pass
    __class_init__ = classmethod(__class_init__)

class PropertyMeta(_GObjectClassInittableMetaType):
    """
    Metaclass that takes into account properties and signals
    of baseclasses, even if they're not GObject subclasses.
    Which allows you to put signals and properties in mixin
    classes.
    """
    # pylint fails to understand this is a metaclass
    def __init__(self, name, bases, namespace):
        def _update_bases(bases, props, signals):
            for base in bases:
                props.update(getattr(base, '__gproperties__', {}))
                signals.update(getattr(base, '__gsignals__', {}))
                _update_bases(base.__bases__, props, signals)

        for base in bases:
            if issubclass(base, gobject.GObject):
                # This will be fun.
                # Merge in properties and signals from all bases, this
                # is not the default behavior of PyGTK, but we need it
                props = namespace.setdefault('__gproperties__', {})
                signals = namespace.setdefault('__gsignals__', {})

                _update_bases(bases, props, signals)
                break

        # Workaround brokenness in PyGObject meta/type registration
        props = namespace.get('__gproperties__', {})
        signals = namespace.get('__gsignals__', {})
        if hasattr(self, '__gtype__'):
            self.__gproperties__ = props
            self.__gsignals__ = signals
            gtype = self.__gtype__
            # Delete signals and properties which are already
            # present in the list
            signal_names = gobject.signal_list_names(gtype)
            for signal in signals.copy():
                if signal in signal_names :
                    del signals[signal]
            prop_names = [prop.name for prop in gobject.list_properties(gtype)]
            for prop in props.copy():
                if prop in prop_names:
                    del props[prop]

        if HAVE_2_6 and issubclass(self, gobject.GObject):
            gobject.type_register(self)

        _GObjectClassInittableMetaType.__init__(self, name, bases, namespace)

        # The metaclass forgets to remove properties and signals
        self.__gproperties__ = {}
        self.__gsignals__ = {}

class PropertyObject(object):
    """
    I am an object which maps GObject properties to attributes
    To be able to use me, you must also inherit from a
    gobject.GObject subclass.

    Example:

    >>> from kiwi.utils import PropertyObject, gproperty

    >>> class Person(PropertyObject, gobject.GObject):
    >>>     gproperty('name', str)
    >>>     gproperty('age', int)
    >>>     gproperty('married', bool, False)

    >>> test = Test()
    >>> test.age = 20
    >>> test.age
    20
    >>> test.married
    False
    """

    __metaclass__ = PropertyMeta

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

            default_values[prop_name] = pspec.default_value

        cls._default_values.update(default_values)

    __class_init__ = classmethod(__class_init__)

    def _set(self, name, value):
        func = getattr(self, 'prop_set_%s' % name, None)
        if callable(func) and func:
            value = func(value)
        self._attributes[name] = value

    def _get(self, name):
        func = getattr(self, 'prop_get_%s' % name, None)
        if callable(func) and func:
            return func()
        return self._attributes[name]

    def get_attribute_names(self):
        return self._attributes.keys()

    def is_default_value(self, attr, value):
        return self._default_values[attr] == value

    def do_set_property(self, pspec, value):
        prop_name = pspec.name.replace('-', '_')
        self._set(prop_name, value)

    def do_get_property(self, pspec):
        prop_name = pspec.name.replace('-', '_')
        return self._get(prop_name)

def gsignal(name, *args, **kwargs):
    """
    Add a GObject signal to the current object.
    It current supports the following types:
      - str, int, float, long, object, enum
    @param name:     name of the signal
    @type name:      string
    @param args:     types for signal parameters,
      if the first one is a string 'override', the signal will be
      overridden and must therefor exists in the parent GObject.
    @keyword flags: One of the following:
      - gobject.SIGNAL_RUN_FIRST
      - gobject.SIGNAL_RUN_LAST
      - gobject.SIGNAL_RUN_CLEANUP
      - gobject.SIGNAL_NO_RECURSE
      - gobject.SIGNAL_DETAILED
      - gobject.SIGNAL_ACTION
      - gobject.SIGNAL_NO_HOOKS
    @keyword retval: return value in signal callback
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

def _max(c):
    # Python 2.3 does not like bitshifting here
    return 2 ** ((8 * struct.calcsize(c)) - 1) - 1

_MAX_VALUES = {int : _max('i'),
               float : _max('f'),
               long : _max('l') }
_DEFAULT_VALUES = {str : '', float : 0.0, int : 0, long : 0L}

def gproperty(name, ptype, default=None, nick='', blurb='',
              flags=gobject.PARAM_READWRITE, **kwargs):
    """
    Add a GObject property to the current object.
    @param name:   name of property
    @type name:    string
    @param ptype:   type of property
    @type ptype:    type
    @param default:  default value
    @param nick:     short description
    @param blurb:    long description
    @param flags:    parameter flags, one of:
      - PARAM_READABLE
      - PARAM_READWRITE
      - PARAM_WRITABLE
      - PARAM_CONSTRUCT
      - PARAM_CONSTRUCT_ONLY
      - PARAM_LAX_VALIDATION
    Optional, only for int, float, long types:
    @keyword minimum:  minimum allowed value
    @keyword maximum:  maximum allowed value
    """

    # General type checking
    if default is None:
        default = _DEFAULT_VALUES.get(ptype)
    elif not isinstance(default, ptype):
        raise TypeError("default must be of type %s, not %r" % (
            ptype, default))
    if not isinstance(nick, str):
        raise TypeError('nick for property %s must be a string, not %r' % (
            name, nick))
    nick = nick or name
    if not isinstance(blurb, str):
        raise TypeError('blurb for property %s must be a string, not %r' % (
            name, blurb))

    # Specific type checking
    if ptype == int or ptype == float or ptype == long:
        default = (kwargs.get('minimum', ptype(0)),
                   kwargs.get('maximum', _MAX_VALUES[ptype]),
                   default)
    elif ptype == bool:
        if (default is not True and
            default is not False):
            raise TypeError("default must be True or False, not %r" % (
                default))
        default = default,
    elif gobject.type_is_a(ptype, gobject.GEnum):
        if default is None:
            raise TypeError("enum properties needs a default value")
        elif not isinstance(default, ptype):
            raise TypeError("enum value %s must be an instance of %r" %
                            (default, ptype))
        default = default,
    elif ptype == str:
        default = default,
    elif ptype == object:
        if default is not None:
            raise TypeError("object types does not have default values")
        default = ()
    else:
        raise NotImplementedError("type %r" % ptype)

    if flags not in (gobject.PARAM_READABLE, gobject.PARAM_READWRITE,
                     gobject.PARAM_WRITABLE, gobject.PARAM_CONSTRUCT,
                     gobject.PARAM_CONSTRUCT_ONLY,
                     gobject.PARAM_LAX_VALIDATION):
        raise TypeError("invalid flag value: %r" % flags)

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
        dict = locals.setdefault('__gproperties__', {})
    finally:
        del frame

    dict[name] = (ptype, nick, blurb) + default + (flags,)
