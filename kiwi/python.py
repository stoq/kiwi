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

"""Generic python addons"""

import unicodedata
import sys
import warnings

__all__ = ['ClassInittableMetaType', 'ClassInittableObject']


class ClassInittableMetaType(type):
    # pylint fails to understand this is a metaclass
    def __init__(self, name, bases, namespace):
        type.__init__(self, name, bases, namespace)
        self.__class_init__(namespace)


class ClassInittableObject(object):
    """
    I am an object which will call a classmethod called
    __class_init__ when I am created.
    Subclasses of me will also have __class_init__ called.

    Note that __class_init__ is called when the class is created,
    eg when the file is imported at the first time.
    It's called after the class is created, but before it is put
    in the namespace of the module where it is defined.
    """
    __metaclass__ = ClassInittableMetaType

    @classmethod
    def __class_init__(cls, namespace):
        """
        Called when the class is created

        :param cls:       class
        :param namespace: namespace for newly created
        :type  namespace: dict
        """


class _ForwardedProperty(object):
    def __init__(self, attribute):
        self._attribute = attribute

    def __get__(self, instance, klass):
        if instance is None:
            return self

        return getattr(instance.target, self._attribute)

    def __set__(self, instance, value):
        if instance is None:
            raise TypeError

        setattr(instance.target, self._attribute, value)


class AttributeForwarder(ClassInittableObject):
    """
    AttributeForwarder is an object which is used to forward certain
    attributes to another object.

    :cvar attributes: list of attributes to be forwarded
    :ivar target: forwarded object
    """
    attributes = None

    @classmethod
    def __class_init__(cls, ns):
        if cls.__bases__ == (ClassInittableObject,):
            return

        if not 'attributes' in ns:
            raise TypeError(
                "the class variable attributes needs to be set for %s" % (
                    cls.__name__))
        if "target" in ns['attributes']:
            raise TypeError("'target' is a reserved attribute")

        for attribute in ns['attributes']:
            setattr(cls, attribute, _ForwardedProperty(attribute))

    def __init__(self, target):
        """
        Create a new AttributeForwarder object.

        :param target: object to forward attributes to
        """
        self.target = target


# copied from twisted/python/reflect.py
def namedAny(name):
    """Get a fully named package, module, module-global object, or attribute.

    :param name:
    :returns: object, module or attribute
    """

    names = name.split('.')
    topLevelPackage = None
    moduleNames = names[:]
    while not topLevelPackage:
        try:
            trialname = '.'.join(moduleNames)
            topLevelPackage = __import__(trialname)
        except ImportError:
            # if the ImportError happened in the module being imported,
            # this is a failure that should be handed to our caller.
            # count stack frames to tell the difference.
            import traceback
            exc_info = sys.exc_info()
            if len(traceback.extract_tb(exc_info[2])) > 1:
                try:
                    # Clean up garbage left in sys.modules.
                    del sys.modules[trialname]
                except KeyError:
                    # Python 2.4 has fixed this.  Yay!
                    pass
                raise exc_info[0], exc_info[1], exc_info[2]
            moduleNames.pop()

    obj = topLevelPackage
    for n in names[1:]:
        obj = getattr(obj, n)

    return obj


class Settable:
    """
    A mixin class for syntactic sugar.  Lets you assign attributes by
    calling with keyword arguments; for example, C{x(a=b,c=d,y=z)} is the
    same as C{x.a=b;x.c=d;x.y=z}.  The most useful place for this is
    where you don't want to name a variable, but you do want to set
    some attributes; for example, C{X()(y=z,a=b)}.
    """
    def __init__(self, **kw):
        self._attrs = kw.keys()
        self._attrs.sort()
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def getattributes(self):
        """
        Fetches the attributes used to create this object
        :returns: a dictionary with attributes
        """
        return self._attrs

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            ', '.join(['%s=%r' % (attr, getattr(self, attr)) for
                                       attr in self._attrs]))


def qual(klass):
    """
    Convert a class to a string representation, which is the name of the module
    plut a dot plus the name of the class.

    :returns: fully qualified module and class name
    """
    return klass.__module__ + '.' + klass.__name__


def clamp(x, low, high):
    """
    Ensures that x is between the limits set by low and high.
    For example,
    * clamp(5, 10, 15) is 10.
    * clamp(15, 5, 10) is 10.
    * clamp(20, 15, 25) is 20.

    :param    x: the value to clamp.
    :param  low: the minimum value allowed.
    :param high: the maximum value allowed.
    :returns: the clamped value
    """

    return min(max(x, low), high)


def slicerange(slice, limit):
    """Takes a slice object and returns a range iterator

    :param slice: slice object
    :param limit: maximum value allowed
    :returns: iterator
    """

    return xrange(*slice.indices(limit))

_no_deprecation = False


def deprecationwarn(msg, stacklevel=2):
    """
    Prints a deprecation warning
    """
    global _no_deprecation
    if _no_deprecation:
        return

    warnings.warn(msg, DeprecationWarning, stacklevel=stacklevel)


def disabledeprecationcall(func, *args, **kwargs):
    """
    Disables all deprecation warnings during the function call to func
    """
    global _no_deprecation
    old = _no_deprecation
    _no_deprecation = True
    retval = func(*args, **kwargs)
    _no_deprecation = old
    return retval


class enum(int):
    """
    enum is an enumered type implementation in python.

    To use it, define an enum subclass like this:

    >>> class Status(enum):
    ...     OPEN, CLOSE = range(2)
    >>> Status.OPEN
    '<Status value OPEN>'

    All the integers defined in the class are assumed to be enums and
    values cannot be duplicated
    """

    __metaclass__ = ClassInittableMetaType

    @classmethod
    def __class_init__(cls, ns):
        cls.names = {}  # name -> enum
        cls.values = {}  # value -> enum

        for key, value in ns.items():
            if isinstance(value, int):
                cls(value, key)

    @classmethod
    def get(cls, value):
        """
        Lookup an enum by value
        :param value: the value
        """
        if not value in cls.values:
            raise ValueError("There is no enum for value %d" % (value,))
        return cls.values[value]

    def __new__(cls, value, name):
        """
        Create a new Enum.

        :param value: value of the enum
        :param name: name of the enum
        """
        if name in cls.names:
            raise ValueError("There is already an enum called %s" % (name,))

        if value in cls.values:
            raise ValueError(
                "Error while creating enum %s of type %s, "
                "it has already been created as %s" % (
                    value, cls.__name__, cls.values[value]))

        self = super(enum, cls).__new__(cls, value)
        self.name = name

        cls.values[value] = self
        cls.names[name] = self
        setattr(cls, name, self)

        return self

    def __str__(self):
        return '<%s value %s>' % (
            self.__class__.__name__, self.name)
    __repr__ = __str__


def all(seq):
    """
    Predict used to check if all items in a seq are True.
    :returns: True if all items in seq are True
    """
    for item in seq:
        if not item:
            return False
    return True


def any(seq):
    """
    Predict used to check if any item in a seq are True.
    :returns: True if any item in seq is True
    """
    for item in seq:
        if item:
            return True
    return False


def strip_accents(string):
    """Remove the accentuantion of a string

    Taken from http://www.python.org.br/wiki/RemovedorDeAcentos

    :param string: a string, either in str or unicode format
    :returns: the string without accentuantion
    """
    if isinstance(string, str):
        # unicode don't need this
        string = string.decode('utf-8')

    string = unicodedata.normalize('NFKD', string)
    return string.encode('ASCII', 'ignore')
