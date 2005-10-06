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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

import inspect

class CustomType(type):
    def value_check(cls, name, value):
        pass
    value_check = classmethod(value_check) 

class number(CustomType):
    type = int, float
    
class percent(CustomType):
    type = int, float
    def value_check(cls, name, value):
        if 0 > value < 100:
            raise ValueError("%s must be between 0 and 100" % name)
    value_check = classmethod(value_check) 
       
class argcheck(object):
    __enabled__ = True
    
    def __init__(self, *types):
        for argtype in types:
            if not isinstance(argtype, type):
                raise TypeError("must be a type instance")
        self.types = types

    def enable(cls):
        """
        Enable argcheck globally
        """
        cls.__enabled__ = True
    enable = classmethod(enable)
    
    def disable(cls):
        """
        Disable argcheck globally
        """
        cls.__enabled__ = False
    disable = classmethod(disable)
        
    def __call__(self, func):
        if not callable(func):
            raise TypeError("%r must be callable" % func)
        
        spec = inspect.getargspec(func)
        arg_names, is_varargs, is_kwargs, default_values = spec
        if is_kwargs and not is_varargs and self.types:
            raise TypeError("argcheck cannot be used with only keywords")
        
        types = self.types
        defs = len(default_values or ())

        kwarg_types = {}
        for i, arg_name in enumerate(arg_names):
            kwarg_types[arg_name] = types[i]
            
            pos = defs - i
            if defs and pos < defs:
                value = default_values[pos]
                arg_type = types[pos]
                try:
                    self._type_check(value, arg_type, arg_name)
                except TypeError:
                    raise TypeError("default value for %s must be of type %s "
                                    "and not %s" % (arg_name,
                                                    arg_type.__name__,
                                                    type(value).__name__))
        if not is_varargs:
            if len(types) != len(arg_names):
                raise TypeError("%s has wrong number of arguments, "
                                "%d specified in decorator, "
                                "but function has %d" %
                                (func.__name__,
                                 len(types),
                                 len(arg_names)))
        
        def wrapper(*args, **kwargs):
            if self.__enabled__:
                # Positional arguments
                for arg, type, name in zip(args, types, arg_names):
                    self._type_check(arg, type, name)

                # Keyword arguments
                for name, arg in kwargs.items():
                    self._type_check(arg, kwarg_types[name], name)
                
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def _type_check(self, value, argument_type, name):
        if issubclass(argument_type, CustomType):
            custom = True
            check_type = argument_type.type
        else:
            custom = False
            check_type = argument_type
            
        type_name = argument_type.__name__

        if not isinstance(value, check_type):
            raise TypeError(
                "%s must be %s, not %s" % (name, type_name,
                                           type(value).__name__))
        if custom:
            argument_type.value_check(name, value)


