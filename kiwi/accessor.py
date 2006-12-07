#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2002-2005 Async Open Source
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
# Author(s): Andreas Kostyrka <andreas@mtg.co.at>
#            Christian Reis <kiko@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""The accessor module offers two important front-end functions:
kgetattr and ksetattr. These functions allow retrieving attribute values
from objects much in the same way as getattr/setattr allow, but with two
important differences:
    - They follow a dot hierarchy to retrieve or modify any value
      reachable from the object.
    - They cache the method used to access a certain attribute and reuse
      it the next time the value is retrieved.
"""

import string
import types

from kiwi.log import Logger

log = Logger('kiwi.accessor')

def get_default_getter(model, attr_name, cache):
    """Obtains from model a callable through which attr_name can be
    retrieved.  This callable is an accessor named get_foo, where
    foo is the value of attr_name, or getattr(model, foo) if the
    accessor does not exist. If the callable exists, it is returned;
    if getattr() is to be used a tuple in the format (model,
    attr_name) is returned."""
    func = getattr(model, "get_%s" % attr_name, None)
    if callable(func):
        log.info('kgetattr based get_%s method is deprecated, '
                 'replace it with a property' % attr_name)
        return func
    else:
        return (model, attr_name)

def get_default_setter(model, attr_name, cache):
    """Obtains from model a callable through which attr_name can be
    set.  This callable is an accessor named set_foo, where
    foo is the value of attr_name, or setattr(model, foo, value) if the
    accessor does not exist. If the callable exists, it is returned;
    if setattr() is to be used a tuple in the format (model,
    attr_name) is returned."""
    func = getattr(model, "set_%s" % attr_name, None)
    if callable(func):
        log.info('ksetattr based set_%s method is deprecated, '
                 'replace it with a property' % attr_name)
        return func
    else:
        return (model, attr_name)

# The _*_cache dictionaries cache the objects, attributes and callables
# (called `accessor tuples' here) we retrieve values from. If possible,
# we use weakrefs to avoid holding hard references to objects, allowing
# them to be garbage collected.  Certain objects (ZODB.Persistent for
# one) cannot be weakref()ed and *will* leak - be sure to call
# clear_attr_cache() if you need them released.
#
# Key structure:
#   (objref_or_weakref, attrname)
#
# Value structure (accessor tuples):
#
#   kgetattr: (access_code, data1, data2)
#   ksetattr: (access_code, data1, data2, value_mode)
#
# Access codes:
#
# 0: data1()                 unbound methods and functions (data2 is None)
# 1: data2(data1())          bound methods and weakref
# 2: getattr(data1(), data2) using straight getattr and weakref
# 3: data2(data1)            bound methods (no weakref)
# 4: getattr(data1, data2)   using straight getattr (no weakref)

import weakref
_kgetattr_cache = {}
_kgetattr_wref = {}
_ksetattr_cache = {}
_ksetattr_wref = {}

class CacheControl(object):
    __slots__ = ['key', 'cacheable']
    def __init__(self, key):
        self.key = key
        self.cacheable = 1

    def disable(self):
        self.cacheable = 0

    def invalidate(self):
        key = self.key
        if _kgetattr_cache.has_key(key):
            del _kgetattr_cache[key]
        if _ksetattr_cache.has_key(key):
            del _ksetattr_cache[key]

class _AttrUnset:
    # indicates an unset value since None needs to be used
    pass

class DefaultValue(Exception):
    """
    This can be raised in kgetattr accessors to indicate that the default
    value should be used
    """

def kgetattr_guard(wref):
    try:
        key = _kgetattr_wref[id(wref)][0]
        del _kgetattr_wref[id(wref)]
        del _kgetattr_cache[key]
    except KeyError:
        # This path is used only when the program terminates.
        pass

def ksetattr_guard(wref):
    try:
        key = _ksetattr_wref[id(wref)][0]
        del _ksetattr_wref[id(wref)]
        del _ksetattr_cache[key]
    except KeyError:
        # This path is used only when the program terminates.
        pass

# 1. Break up attr_name into parts
# 2. Loop around main lookup code for each part:
#     2.1. Try and get accessor tuple out of cache
#     2.2. If not there, generate tuple from callable and store it
#     2.3. Use accessor tuple to grab value
#     2.4. Value wasn't found, return default or raise ValueError
#   Use value as obj in next iteration
# 3. Return value

def kgetattr(model,
             attr_name,
             default=_AttrUnset,
             flat=0,
             # bind to local variables for speed:
             ref=weakref.ref,
             TupleType=types.TupleType,
             MethodType=types.MethodType,
             split=string.split,
             kgetattr_guard=kgetattr_guard,
             getattr=getattr,
             dummycache=CacheControl((None,None)),
             # constants:
             # access opcodes:
             LAMBDA_ACCESS = 0,
             METHOD_ACCESS = 1,
             TUPLE_ACCESS = 2,
             NWR_METHOD_ACCESS = 3,
             NWR_TUPLE_ACCESS = 4,
             # FAST tuples do not store the object, as the input object
             # is also the accesses object.
             FAST_METHOD_ACCESS = 5,
             FAST_TUPLE_ACCESS = 6,
             ):
    """Returns the value associated with the attribute in model
    named by attr_name. If default is provided and model does not
    have an attribute called attr_name, the default value is
    returned. If flat=1 is specified, no dot path parsing will
    be done."""

    # 1. Break up attr_name into parts
    if flat or "." not in attr_name:
        names = [attr_name, ]
    else:
        try:
            names = attr_name.split(".")
        except AttributeError:
            names = split(attr_name, ".")

    # 2. Loop around main lookup code for each part:
    obj = model
    for name in names:
        key = (id(obj), name)
        # First time round, obj is the model. Every subsequent loop, obj
        # is the subattribute value indicated by the current part in
        # [names]. The last loop grabs the target value and returns it.

        try:
            # 2.1 Fetch the opcode tuple from the cache.
            objref, icode, data1, data2 = _kgetattr_cache[key]
        except KeyError:
            # 2.2. If not there, generate tuple from callable and store it
            try:
                get_getter = obj.__class__.get_getter
                cache = CacheControl(key)
            except AttributeError:
                # This is needed so that the check below if the result is
                # cacheable can be done. The inbuilt get_getter always
                # allows caching.
                cache = dummycache
                get_getter = None

                func = getattr(obj, "get_%s" % name, None)
                if callable(func):
                    log.info('kgetattr based get_%s method is deprecated, '
                             'replace it with a property' % name)
                    icode = FAST_METHOD_ACCESS
                    data1 = func.im_func
                    data2 = None
                else:
                    icode = FAST_TUPLE_ACCESS
                    data1 = None
                    data2 = name

            if get_getter is not None:
                try:
                    func = get_getter(obj, name, cache)
                except DefaultValue:
                    if default == _AttrUnset:
                        raise
                    return default

                if isinstance(func, TupleType):
                    data1, data2 = func
                    if data1 == obj:
                        data1 = None
                        icode = FAST_TUPLE_ACCESS
                    else:
                        try:
                            data1 = ref(data1, kgetattr_guard)
                            _kgetattr_wref[id(data1)] = (key, data1)
                            icode = TUPLE_ACCESS
                        except TypeError:
                            icode = NWR_TUPLE_ACCESS

                elif isinstance(func, MethodType):
                    data1 = func.im_func
                    data2 = func.im_self
                    if data2 == obj:
                        data2 = None
                        icode = FAST_METHOD_ACCESS
                    else:
                        try:
                            data2 = ref(func.im_self, kgetattr_guard)
                            _kgetattr_wref[id(data2)] = (key, data2)
                            icode = METHOD_ACCESS
                        except TypeError:
                            data2 = func.im_self
                            icode = NWR_METHOD_ACCESS
                else:
                    icode = LAMBDA_ACCESS
                    data1 = func
                    data2 = None
            if cache.cacheable:
                # Store access opcode:
                # objref or obj are used as a protection against id-aliasing
                # as we use just a plain id(obj) in the cache entry key.
                #
                # We either have to use a weakref, so we get to know when the
                # object dies. We just remove the cache entry containing the
                # weakref, _kgetattr_wref is used to associate which key has
                # to be killed for a given weakref.

                try:
                    objref = ref(obj, kgetattr_guard)
                    _kgetattr_wref[id(objref)] = (key, objref)
                    _kgetattr_cache[key] = (objref, icode, data1, data2)
                except TypeError:
                    # it's not weakrefable (probably ZODB!)
                    # store a hard reference.
                    _kgetattr_cache[key] = (obj, icode, data1, data2)
            else:
                if _kgetattr_cache.has_key(key):
                    del _kgetattr_cache[key]

        # 2.3. Use accessor tuple to grab value
        try:
            if icode == FAST_METHOD_ACCESS:
                obj = data1(obj)
            elif icode == FAST_TUPLE_ACCESS:
                obj = getattr(obj, data2, default)
                if obj is _AttrUnset:
                    raise AttributeError(
                        "%r object has no attribute %r" % (obj, data2))
            elif icode == TUPLE_ACCESS:
                o = data1()
                obj = getattr(o, data2, default)
                if obj is _AttrUnset:
                    raise AttributeError(
                        "%r object has no attribute %r" % (o, data2))
            elif icode == NWR_TUPLE_ACCESS:
                obj = getattr(data1, data2)
            elif icode == NWR_METHOD_ACCESS:
                obj = data1(data2)
            elif icode == METHOD_ACCESS:
                obj = data1(data2())
            elif icode == LAMBDA_ACCESS:
                obj = data1()
            else:
                raise AssertionError("Unknown tuple type in _kgetattr_cache")

        # 2.4. Value wasn't found, return default or raise ValueError
        except DefaultValue:
            if default == _AttrUnset:
                raise
            return default

        # At the end of the iteration, the value retrieved becomes the new obj

    # 3. Return value
    return obj

# A general algo for ksetattr:
#
# 1. Use attr_name to kgetattr the target object, and get the real attribute
# 2. Try and get accessor tuple from cache
# 3. If not there, generate accessor tuple and store it
# 4. Set value to target object's attribute

def ksetattr(model,
             attr_name,
             value,
             flat=0,

             # bind to local variables for speed:
             ref=weakref.ref,
             TupleType=types.TupleType,
             MethodType=types.MethodType,
             ksetattr_guard=ksetattr_guard,
             getattr=getattr,
             dummycache=CacheControl((None,None)),

             # constants:
             LAMBDA_ACCESS = 0,
             METHOD_ACCESS = 1,
             TUPLE_ACCESS = 2,
             NWR_METHOD_ACCESS = 3,
             NWR_TUPLE_ACCESS = 4,
             FAST_METHOD_ACCESS = 5,
             FAST_TUPLE_ACCESS = 6,
                 ):
    """Set the value associated with the attribute in model
    named by attr_name. If flat=1 is specified, no dot path parsing will
    be done."""

    # 1. kgetattr the target object, and get the real attribute
    # This is the only section which is special about ksetattr. When you
    # set foo.bar.baz to "x", what you really want to do is get hold of
    # foo.bar and use an accessor (set_baz/setattr) on it. This bit gets
    # the attribute name and the model we want.

    if not flat:
        lastdot = string.rfind(attr_name, ".")
        if lastdot != -1:
            model = kgetattr(model, attr_name[:lastdot])
            attr_name = attr_name[lastdot+1:]

    # At this point we only have a flat attribute and the right model.
    key = (id(model), attr_name)

    try:
        # 2. Try and get accessor tuple from cache
        objref, icode, data1, data2 = _ksetattr_cache[key]
    except KeyError:
        # 3. If not there, generate accessor tuple and store it
        #    cache = CacheControl(key)
        try:
            get_setter = model.__class__.get_setter
            cache = CacheControl(key)
        except AttributeError:
            # No get_setter found:
            get_setter = None
            # This is needed so the entry storing code can check if it's ok
            # to cache.
            cache = dummycache

            func = getattr(model, "set_%s" % attr_name, None)
            if callable(func):
                log.info('ksetattr based set_%s method is deprecated, '
                         'replace it with a property' % attr_name)
                icode = FAST_METHOD_ACCESS
                data1 = func.im_func
                data2 = None
            else:
                icode = FAST_TUPLE_ACCESS
                data1 = None
                data2 = attr_name

        if get_setter is not None:
            func = get_setter(model, attr_name, cache)

            if isinstance(func, TupleType):
                data1, data2 = func
                if data1 == model:
                    data1 = None
                    icode = FAST_TUPLE_ACCESS
                else:
                    try:
                        data1 = ref(data1, ksetattr_guard)
                        _ksetattr_wref[id(data1)] = (key, data1)
                        icode = TUPLE_ACCESS
                    except TypeError:
                        icode = NWR_TUPLE_ACCESS
            elif isinstance(func, MethodType):
                data1 = func.im_func
                data2 = func.im_self
                if data2 == model:
                    data2 = None
                    icode = FAST_METHOD_ACCESS
                else:
                    try:
                        data2 = ref(data2, ksetattr_guard)
                        _ksetattr_wref[id(data2)] = (key, data2)
                        icode = METHOD_ACCESS
                    except TypeError:
                        data2 = func.im_self
                        icode = NWR_METHOD_ACCESS
            else:
                icode = LAMBDA_ACCESS
                data1 = func
                data2 = None

        if cache.cacheable:
            # store the access opcode.
            # for the use of model/objref as first value in the opcode tuple
            # see the kgetattr comments.
            try:
                objref = ref(model, ksetattr_guard)
                _ksetattr_wref[id(objref)] = (key, objref)
                _ksetattr_cache[key] = (objref, icode, data1, data2)
            except TypeError:
                # it's not weakref-able, store a hard reference.
                _ksetattr_cache[key] = (model, icode, data1, data2)
        else:
            if _ksetattr_cache.has_key(key):
                del _ksetattr_cache.has_key[key]

    if icode == FAST_TUPLE_ACCESS:
        setattr(model, data2, value)
    elif icode == FAST_METHOD_ACCESS:
        data1(model, value)
    elif icode == TUPLE_ACCESS:
        setattr(data1(), data2, value)
    elif icode == NWR_TUPLE_ACCESS:
        setattr(data1, data2, value)
    elif icode == NWR_METHOD_ACCESS:
        data1(data2, value)
    elif icode == METHOD_ACCESS:
        data1(data2(), value)
    elif icode == LAMBDA_ACCESS:
        data1(value)
    else:
        raise AssertionError("Unknown tuple type in _ksetattr_cache")

def enable_attr_cache():
    """Enables the use of the kgetattr cache when using Python
    versions that do not support weakrefs (1.5.x and earlier). Be
    warned, using the cache in these versions causes leaked
    references to accessor methods and models!"""
    global _kgetattr_cache, _ksetattr_cache, _kgetattr_wref, _ksetattr_wref
    _kgetattr_cache = {}
    _ksetattr_cache = {}
    _kgetattr_wref = {}
    _ksetattr_wref = {}

def clear_attr_cache():
    """Clears the kgetattr cache. It must be called repeatedly to
    avoid memory leaks in Python 2.0 and earlier."""
    global _kgetattr_cache, _ksetattr_cache, _kgetattr_wref, _ksetattr_wref
    _kgetattr_cache = {}
    _ksetattr_cache = {}
    _kgetattr_wref = {}
    _ksetattr_wref = {}
