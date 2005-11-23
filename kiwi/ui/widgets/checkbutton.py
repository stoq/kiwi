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

"""GtkCheckButton support for the Kiwi Framework"""

import gtk

from kiwi import ValueUnset
from kiwi.ui.widgets.proxy import WidgetMixin
from kiwi.utils import PropertyObject, gsignal

class CheckButton(PropertyObject, gtk.CheckButton, WidgetMixin):
    # changed allowed data types because checkbuttons can only
    # accept bool values
    allowed_data_types = bool,
    
    def __init__(self):
        WidgetMixin.__init__(self)
        PropertyObject.__init__(self, data_type=bool)
        gtk.CheckButton.__init__(self)
        self.show()
    
    gsignal('toggled', 'override')
    def do_toggled(self):
        self.emit('content-changed')
        self.chain()
        
    def read(self):
        return self.get_active()

    def update(self, data):
        if data is not ValueUnset and data is not None:
            self.set_active(data)
