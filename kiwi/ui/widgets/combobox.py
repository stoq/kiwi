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
# Author(s): Christian Reis <kiko@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""GtkComboBox and GtkComboBoxEntry support for the Kiwi Framework.
backwards compatibility layer"""

from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.combo import ProxyComboBoxEntry

class ComboBox(ProxyComboBox):
    pass

class ComboBoxEntry(ProxyComboBoxEntry):
    pass
