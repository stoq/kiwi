#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2006 Async Open Source
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

"""High level wrapper for GtkTreeView: backwards compatibility layer"""

import gtk

from kiwi.python import deprecationwarn
from kiwi.ui.objectlist import Column, SequentialColumn, ColoredColumn, \
     ListLabel, SummaryLabel
from kiwi.ui.objectlist import ObjectList

# pyflakes
Column, SequentialColumn, ColoredColumn, ListLabel, SummaryLabel

class List(ObjectList):
    def __init__(self, columns=[],
                 instance_list=None,
                 mode=gtk.SELECTION_BROWSE):
        deprecationwarn(
            'ProxyComboBoxEntry is deprecated, use ProxyComboEntry instead',
            stacklevel=3)
        ObjectList.__init__(self, columns, instance_list, mode)
