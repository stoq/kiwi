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

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.datatypes import number
from kiwi.python import deprecationwarn
from kiwi.ui.proxywidget import ValidatableProxyWidgetMixin
from kiwi.utils import gsignal, type_register

class ProxyTextView(gtk.TextView, ValidatableProxyWidgetMixin):
    __gtype_name__ = 'ProxyTextView'
    data_value = gobject.property(type=str, nick='Data Value')
    data_type = gobject.property(
        getter=ValidatableProxyWidgetMixin.get_data_type,
        setter=ValidatableProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    mandatory = gobject.property(type=bool, default=False)
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)
    allowed_data_types = (basestring, datetime.date) + number
    def __init__(self):
        self._is_unset = True
        gtk.TextView.__init__(self)
        self.props.data_type = str
        ValidatableProxyWidgetMixin.__init__(self)

        self._textbuffer = gtk.TextBuffer()
        self._textbuffer.connect('changed',
                                 self._on_textbuffer__changed)
        self.set_buffer(self._textbuffer)

    def _on_textbuffer__changed(self, textbuffer):
        self._is_unset = False
        self.emit('content-changed')
        self.read()

    def read(self):
        if self._is_unset:
            return ValueUnset
        textbuffer = self._textbuffer
        data = textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter())
        return self._from_string(data)

    def update(self, data):
        if data is ValueUnset:
            self._textbuffer.set_text("")
            self._is_unset = True
            return
        elif data is None:
            text = ""
        else:
            self.is_unset = False
            text = self._as_string(data)

        self._textbuffer.set_text(text)

class TextView(ProxyTextView):
    def __init__(self):
        deprecationwarn(
            'TextView is deprecated, use ProxyTextView instead',
            stacklevel=3)
        ProxyTextView.__init__(self)
type_register(TextView)
