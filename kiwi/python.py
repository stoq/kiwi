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

__all__ = ['ClassInittableObject']

class _ClassInittableMetaType(type):
    def __init__(cls, name, bases, namespace):
        super(_ClassInittableMetaType, cls).__init__(name, bases, namespace)
        cls.__class_init__(namespace)

class ClassInittableObject(object):
    """
    I am an object which will call a classmethod called
    __class_init__ when I am created.
    """
    __metaclass__ = _ClassInittableMetaType

    def __class_init__(cls, namespace):
        """
        Called when the class is created

        @param cls:       class
        @param namespace: namespace for newly created
        @type  namespace: dict
        """
    __class_init__ = classmethod(__class_init__)
