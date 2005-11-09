#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
#            Daniel Saran R. da Cunha <daniel@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#

"""Defines an enhanced version of GtkRadioButton"""

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy
from kiwi.utils import gsignal, gproperty, type_register
from kiwi.ui.widgets.proxy import WidgetMixin

class RadioButton(gtk.RadioButton, WidgetMixin):
    implementsIProxy()
    gproperty('data-value', str, nick='Data Value')

    def __init__(self):
        WidgetMixin.__init__(self)
        gtk.RadioButton.__init__(self)
        self._data_value = None
        self.show()
    
    gsignal('toggled', 'override')
    def do_toggled(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        for rb in self.get_group():
            if rb.get_active():
                return self.str2type(rb.get_property('data-value'))

    def update(self, data):
        if data is None or data is ValueUnset:
            return
        data = self.type2str(data)
        for rb in self.get_group():
            if rb.get_property('data-value') == data:
                rb.set_active(True)
    
    def prop_set_data_value(self, data):
        self._data_value = data
    
    def prop_get_data_value(self):
        return self._data_value

type_register(RadioButton)
