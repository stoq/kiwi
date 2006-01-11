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

"""Generic python addons"""

import os
import sys

import gobject

# When we can depend on 2.8 clean this up, so ClassInittable does not
# need to be tied to GObjectMeta, since it doesn't need to be a GObject
# Always use type for epydoc, since GObjectMeta creates lots of trouble
# for us when using fake objects.
if (gobject.pygtk_version >= (2, 7, 0) and
    os.path.basename(sys.argv[0]) != 'epyrun'):
    metabase = gobject.GObjectMeta
else:
    metabase = type

__all__ = ['ClassInittableMetaType', 'ClassInittableObject']

class ClassInittableMetaType(metabase):
    # pylint fails to understand this is a metaclass
    def __new__(cls, name, bases, namespace):
        c = metabase.__new__(cls, name, bases, namespace)
        c.__class_init__(namespace)
        return c
    
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

    def __class_init__(cls, namespace):
        """
        Called when the class is created

        @param cls:       class
        @param namespace: namespace for newly created
        @type  namespace: dict
        """
    __class_init__ = classmethod(__class_init__)

# copied from twisted/python/reflect.py
def namedAny(name):
    """Get a fully named package, module, module-global object, or attribute.
    
    @param name:
    @returns: object, module or attribute
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

def qual(klass):
    """
    @returns: fully qualified module and class name
    """
    return klass.__module__ + '.' + klass.__name__

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
    @returns: the clamped value
    """
    
    return min(max(x, low), high)

def slicerange(slice, limit):
    """Takes a slice object and returns a range iterator

    @param slice: slice object
    @param limit: maximum value allowed
    @returns: iterator
    """
    
    return xrange(*slice.indices(limit))
