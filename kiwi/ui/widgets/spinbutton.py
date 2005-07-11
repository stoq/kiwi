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

import time

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy, implementsIMandatoryProxy
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import gsignal

class SpinButton(gtk.SpinButton, WidgetMixinSupportValidation):
    implementsIProxy()
    implementsIMandatoryProxy()

    gsignal('changed', 'override')
    # mandatory widgets need to have this signal connected
    gsignal('expose-event', 'override')
    
    def __init__(self):
        # since the default data_type is str we need to set it to int 
        # or float for spinbuttons
        gtk.SpinButton.__init__(self)
        WidgetMixinSupportValidation.__init__(self, data_type=int)
        
        # due to changes on pygtk 2.6 we have to make some ajustments here
        if gtk.pygtk_version < (2,6):
            self.chain_expose = self.chain
        else:
            self.chain_expose = \
                              lambda e: gtk.SpinButton.do_expose_event(self, e)
        
    def prop_set_data_type(self, data_type):
        """Overriden from super class. Since spinbuttons should
        only accept float or int numbers we need to make a special
        treatment.
        """
        old_datatype = self._data_type
        WidgetMixinSupportValidation.set_data_type(self, data_type)
        if self._data_type not in (int, float):
            self._data_type = old_datatype
            raise TypeError("SpinButtons only accept integer or float values")
        
    def do_changed(self):
        self._last_change_time = time.time()
        self.emit('content-changed')
        self.chain()

    def read(self):
        return self.get_text()

    def update(self, data):
        WidgetMixinSupportValidation.update(self, data)
        
        if data is ValueUnset or data is None:
            self.set_text("")
            self.draw_mandatory_icon_if_needed()
        else:
            self.set_value(data)

    def do_expose_event(self, event):
        """Expose-event signal are triggered when a redraw of the widget
        needs to be done.
        
        Draws information and mandatory icons when necessary
        """        
        result = self.chain_expose(event)
        
        # this attribute stores the info on where to draw icons and paint
        # the background
        # it's been defined here because it's when we have gdk window available
        self._draw_icon(self.window)
        
        return result
    
gobject.type_register(SpinButton)
