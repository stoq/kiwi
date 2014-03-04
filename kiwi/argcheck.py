#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005,2006 Async Open Source
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

"""
Argument checking decorator and support
"""

import inspect
from types import ClassType

from kiwi.datatypes import number as number_type

_NoValue = object()


class CustomType(type):
    @classmethod
    def value_check(mcs, name, value):
        pass


class number(CustomType):
    """
    Custom type that verifies that the type is a number (eg float or int)
    """
    type = number_type


class percent(CustomType):
    """
    Custom type that verifies that the value is a percentage
    """
    type = number_type

    @classmethod
    def value_check(mcs, name, value):
        if (value < 0) or (value > 100):
            raise ValueError("%s must be between 0 and 100" % name)


class argcheck(object):
    """
    Decorator to check type and value of arguments.

    Usage:

        >>> @argcheck(int, str)
        ... def function(int_arg, str_arg):
        ...     pass

    or

        >>> class Class:
        ...     @argcheck(int, str)
        ...     def method(self, int_arg, str_arg):
        ...         pass

    You can customize the checks by subclassing your type from CustomType,
    there are two builtin types: number which is a float/int combined check
    and a percent which verifis that the value is a percentage
    """

    __enabled__ = True

    def __init__(self, *types):
        for argtype in types:
            if not isinstance(argtype, (type, ClassType)):
                raise TypeError("must be a type or class instance, not %r" % argtype)
        self.types = types

    @classmethod
    def enable(cls):
        """
        Enable argcheck globally
        """
        cls.__enabled__ = True

    @classmethod
    def disable(cls):
        """
        Disable argcheck globally
        """
        cls.__enabled__ = False

    def __call__(self, func):
        if not callable(func):
            raise TypeError("%r must be callable" % func)

        # Useful for optimized runs
        if not self.__enabled__:
            return func

        spec = inspect.getargspec(func)
        arg_names, is_varargs, is_kwargs, default_values = spec
        if not default_values:
            default_values = []
        else:
            default_values = list(default_values)

        # Set all the remaining default values to _NoValue
        default_values = ([_NoValue] * (len(arg_names) - len(default_values)) +
                          default_values)

        # TODO: Is there another way of doing this?
        #       Not trivial since func is not attached to the class at
        #       this point. Nor is the class attached to the namespace.
        if arg_names and arg_names[0] in ('self', 'cls'):
            arg_names = arg_names[1:]
            default_values = default_values[1:]
            is_method = True
        else:
            is_method = False

        types = self.types
        if is_kwargs and not is_varargs and self.types:
            raise TypeError("argcheck cannot be used with only keywords")
        elif not is_varargs:
            if len(types) != len(arg_names):
                raise TypeError("%s has wrong number of arguments, "
                                "%d specified in decorator, "
                                "but function has %d" %
                                (func.__name__,
                                 len(types),
                                 len(arg_names)))

        kwarg_types = {}
        kwarg_defaults = {}

        for i, arg_name in enumerate(arg_names):
            kwarg_types[arg_name] = types[i]
            value = default_values[i]
            kwarg_defaults[arg_name] = value
            if value is None or value is _NoValue:
                continue
            arg_type = types[i]
            try:
                self._type_check(value, arg_type, arg_name)
            except TypeError:
                raise TypeError("default value for %s must be of type %s "
                                "and not %s" % (arg_name,
                                                arg_type.__name__,
                                                type(value).__name__))
            kwarg_defaults[arg_name] = value

        def wrapper(*args, **kwargs):
            if self.__enabled__:
                cargs = args
                if is_method:
                    cargs = cargs[1:]

                # Positional arguments
                for arg, type, name, default in zip(cargs, types, arg_names,
                                                    default_values):
                    self._type_check(arg, type, name, default)

                # Keyword arguments
                for name, arg in kwargs.items():
                    if not name in kwarg_types:
                        raise TypeError(
                            "%s() got an unexpected keyword argument '%s'"
                            % (func.__name__, name))
                    self._type_check(arg, kwarg_types[name], name,
                                     kwarg_defaults[name])

                self.extra_check(arg_names, types, args, kwargs)
            return func(*args, **kwargs)

        # Python 2.3 does not support assignments to __name__
        try:
            wrapper.__name__ = func.__name__
        except TypeError:
            pass

        return wrapper

    def extra_check(self, names, types, args, kwargs):
        pass

    def _type_check(self, value, argument_type, name, default=_NoValue):
        if default is not _NoValue and value == default:
            return

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
