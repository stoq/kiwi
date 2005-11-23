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

"""GtkRadioButton support for the Kiwi Framework"""

import gtk

from kiwi import ValueUnset
from kiwi.utils import PropertyObject, gsignal, gproperty
from kiwi.ui.widgets.proxy import WidgetMixin

class RadioButton(PropertyObject, gtk.RadioButton, WidgetMixin):
    gproperty('data-value', str, nick='Data Value')

    def __init__(self):
        gtk.RadioButton.__init__(self)
        WidgetMixin.__init__(self)
        PropertyObject.__init__(self)
        self.show()
    
    gsignal('toggled', 'override')
    def do_toggled(self):
        self.emit('content-changed')
        self.chain()

    def get_selected(self):
        """
        Get the currently selected radiobutton.
        
        @returns: The selected L{RadioButton} or None if there are no
          selected radiobuttons.
        """
        
        for button in self.get_group():
            if button.get_active():
                return button

    def read(self):
        button = self.get_selected()
        if button is not None:
            return self._as_string(button.data_value)

    def update(self, data):
        if data is None or data is ValueUnset:
            return
        data = self._from_string(data)
        for rb in self.get_group():
            if rb.get_property('data-value') == data:
                rb.set_active(True)
