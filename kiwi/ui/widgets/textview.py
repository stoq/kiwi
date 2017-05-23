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

import datetime

from gi.repository import Gtk, GObject

from kiwi import ValueUnset
from kiwi.datatypes import number
from kiwi.ui.proxywidget import ValidatableProxyWidgetMixin
from kiwi.utils import gsignal


class ProxyTextView(Gtk.TextView, ValidatableProxyWidgetMixin):
    __gtype_name__ = 'ProxyTextView'
    data_value = GObject.Property(type=str, nick='Data Value')
    data_type = GObject.Property(
        getter=ValidatableProxyWidgetMixin.get_data_type,
        setter=ValidatableProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    mandatory = GObject.Property(type=bool, default=False)
    model_attribute = GObject.Property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)
    allowed_data_types = (str, datetime.date) + number

    def __init__(self):
        Gtk.TextView.__init__(self)
        ValidatableProxyWidgetMixin.__init__(self)

        self.data_type = str
        self._textbuffer = Gtk.TextBuffer()
        self._textbuffer.connect('changed',
                                 self._on_textbuffer__changed)
        self.set_buffer(self._textbuffer)

    def _on_textbuffer__changed(self, textbuffer):
        self.emit('content-changed')
        self.read()

    def read(self):
        textbuffer = self._textbuffer
        data = textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter(),
                                   True)
        return self._from_string(data)

    def update(self, data):
        if data is ValueUnset or data is None:
            text = ""
        else:
            text = self._as_string(data)

        if self.props.mandatory:
            self.emit('validation-changed', bool(text))
        self._textbuffer.set_text(text)

GObject.type_register(ProxyTextView)
