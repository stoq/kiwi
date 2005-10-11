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
#            Gustavo Rahal <gustavo@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#

"""Defines an enhanced version of GtkCheckButton"""

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy
from kiwi.ui.widgets.proxy import WidgetMixin
from kiwi.utils import gsignal

class CheckButton(gtk.CheckButton, WidgetMixin):
    implementsIProxy()
        
    def __init__(self):
        # changed default data_type because checkbuttons can only
        # accept bool values
        WidgetMixin.__init__(self, data_type=bool)
        gtk.CheckButton.__init__(self)
        self.set_property("data-type", bool)
        self.show()
    
    def prop_set_data_type(self, data_type):
        if data_type == bool or data_type is None:
            WidgetMixin.prop_set_data_type(self, data_type)
        else:
            raise TypeError("CheckButtons only accept boolean values")

    gsignal('toggled', 'override')
    def do_toggled(self):
        self.emit('content-changed')
        self.chain()
        
    def read(self):
        return self.get_active()

    def update(self, data):
        # first, trigger some basic validation
        WidgetMixin.update(self, data)
        if data is not ValueUnset and data is not None:
            self.set_active(data)

gobject.type_register(CheckButton)
