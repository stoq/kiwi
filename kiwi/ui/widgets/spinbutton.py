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
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Evandro Vale Miquelito <evandro@async.com.br>
#

"""Defines an enhanced version of GtkSpinButton"""

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy, implementsIMandatoryProxy
from kiwi.ui.icon import IconEntry
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import gsignal, type_register

class SpinButton(gtk.SpinButton, WidgetMixinSupportValidation):
    implementsIProxy()
    implementsIMandatoryProxy()

    def __init__(self):
        # since the default data_type is str we need to set it to int 
        # or float for spinbuttons
        gtk.SpinButton.__init__(self)
        WidgetMixinSupportValidation.__init__(self, data_type=int)
        self._icon = IconEntry(self)
        self.show()
        
    def prop_set_data_type(self, data_type):
        """Overriden from super class. Since spinbuttons should
        only accept float or int numbers we need to make a special
        treatment.
        """
        old_datatype = self._data_type
        WidgetMixinSupportValidation.prop_set_data_type(self, data_type)
        if self._data_type not in (int, float):
            self._data_type = old_datatype
            raise TypeError("SpinButtons only accept integer or float values")

    # GtkEditable.changed is called too often
    # GtkSpinButton.value-changed is called only when the value changes
    gsignal('value-changed', 'override')
    def do_value_changed(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        value = self.get_text()
        return self.validate_data(value)

    def update(self, data):
        if data is ValueUnset or data is None:
            self.set_text("")
        else:
            self.set_value(data)

    def do_expose_event(self, event):
        # This gets called when any of our three windows needs to be redrawn
        gtk.SpinButton.do_expose_event(self, event)

        if event.window == self.window:
            self._icon.draw_pixbuf()

    gsignal('size-allocate', 'override')
    def do_size_allocate(self, allocation):

        self.chain(allocation)
    
	if self.flags() & gtk.REALIZED:
            self._icon.resize_windows()

    def do_realize(self):
        gtk.SpinButton.do_realize(self)
        self._icon.construct()

    def do_unrealize(self):
        self._icon.deconstruct()
        gtk.SpinButton.do_unrealize(self)
        
    # IconEntry
    
    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)
        
    def update_background(self, color):
        self._icon.update_background(color)

    def get_icon_window(self):
        return self._icon.get_icon_window()

type_register(SpinButton)
