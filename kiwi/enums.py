#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006-2007 Async Open Source
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

from kiwi.python import enum


class ComboColumn(enum):
    (LABEL,
     DATA) = range(2)


class ComboMode(enum):
    (UNKNOWN,
     STRING,
     DATA) = range(3)


class Alignment(enum):
    (LEFT,
     RIGHT) = range(2)


class Direction(enum):
    (LEFT, RIGHT) = (1, -1)


class ListType(enum):
    """
    - NORMAL: Add, Remove, Edit
    - READONLY: No buttons
    - ADDONLY: Add
    - REMOVEOLY: Remove
    - UNREMOVABLE: Add, Edit
    - UNADDABLE: Remove, Edit
    - UNEDITABLE: Add, Remove
    """
    (NORMAL,
     READONLY,
     ADDONLY,
     REMOVEONLY,
     UNREMOVABLE,
     UNADDABLE,
     UNEDITABLE) = range(7)
