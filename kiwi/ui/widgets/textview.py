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
#            Evandro Vale Miquelito <evandro@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>

"""GtkTextView support for the Kiwi Framework"""

import gtk

from kiwi import ValueUnset
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import PropertyObject

class TextView(PropertyObject, gtk.TextView, WidgetMixinSupportValidation):
    def __init__(self):
        gtk.TextView.__init__(self)
        PropertyObject.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        
        self.textbuffer = gtk.TextBuffer()
        self.textbuffer.connect('changed',
                                self._on_textbuffer__changed)
        self.set_buffer(self.textbuffer)
        
        self.show()
    
    def _on_textbuffer__changed(self, textbuffer):
        self.emit('content-changed')
        self.read()

    def read(self):
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        return self.textbuffer.get_text(start, end)
                    
    def update(self, data):
        if data is ValueUnset or data is None:
            self.textbuffer.set_text("")
            self.emit('content-changed')
        else:
            self.textbuffer.set_text(self._from_string(data))
