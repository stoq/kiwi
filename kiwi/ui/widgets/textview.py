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

from kiwi.ui.widgets.proxy import ValidatableProxyWidgetMixin
from kiwi.utils import PropertyObject

class TextView(PropertyObject, gtk.TextView, ValidatableProxyWidgetMixin):
    def __init__(self):
        gtk.TextView.__init__(self)
        PropertyObject.__init__(self, data_type=str)
        ValidatableProxyWidgetMixin.__init__(self)

        self._textbuffer = gtk.TextBuffer()
        self._textbuffer.connect('changed',
                                 self._on_textbuffer__changed)
        self.set_buffer(self._textbuffer)

    def _on_textbuffer__changed(self, textbuffer):
        self.emit('content-changed')
        self.read()

    def read(self):
        textbuffer = self._textbuffer
        data = textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter())
        return self._from_string(data)

    def update(self, data):
        if data is None:
            text = ""
        else:
            text = self._as_string(data)

        self._textbuffer.set_text(text)
