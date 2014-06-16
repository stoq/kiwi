#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2006 Async Open Source
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

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.utils import gsignal
from kiwi.ui.proxywidget import ProxyWidgetMixin


class ProxyRadioButton(gtk.RadioButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyRadioButton'
    allowed_data_types = object,
    data_value = gobject.property(type=str, nick='Data Value')
    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self, group=None, label=None, use_underline=True):
        gtk.RadioButton.__init__(self, None, label, use_underline)
        if group:
            self.set_group(group)
        ProxyWidgetMixin.__init__(self)
        self.connect('group-changed', self._on_group_changed)

    def _on_radio__toggled(self, radio):
        self.emit('content-changed')

    def _on_group_changed(self, radio):
        for radio in radio.get_group():
            radio.connect('toggled', self._on_radio__toggled)

    def get_selected(self):
        """
        Get the currently selected radiobutton.

        :returns: The selected :class:`RadioButton` or None if there are no
          selected radiobuttons.
        """

        for button in self.get_group():
            if button.get_active():
                return button

    def read(self):
        button = self.get_selected()
        if button is None:
            return ValueUnset

        return self._from_string(button.data_value)

    def update(self, data):
        if data is None or data is ValueUnset:
            # In a group of radiobuttons, the only widget which is in
            # the proxy is ourself, the other buttons do not get their
            # update() method called, so the default value is activate
            # ourselves when the model is empty
            self.set_active(True)
            return

        data = self._as_string(data)
        for rb in self.get_group():
            if rb.get_property('data-value') == data:
                rb.set_active(True)

gobject.type_register(ProxyRadioButton)
