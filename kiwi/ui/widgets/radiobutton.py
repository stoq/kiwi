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
#from kiwi.python import deprecationwarn
from kiwi.utils import PropertyObject, gproperty
from kiwi.ui.proxywidget import ProxyWidgetMixin

class ProxyRadioButton(PropertyObject, gtk.RadioButton, ProxyWidgetMixin):
    gproperty('data-value', str, nick='Data Value')

    def __init__(self, group=None, label=None, use_underline=True):
        gtk.RadioButton.__init__(self, group, label, use_underline)
        ProxyWidgetMixin.__init__(self)
        PropertyObject.__init__(self)
        self.connect('group-changed', self._on_group_changed)

    def _on_radio__toggled(self, radio):
        self.emit('content-changed')

    def _on_group_changed(self, radio):
        for radio in radio.get_group():
            radio.connect('toggled', self._on_radio__toggled)

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
        if button is None:
            return ValueUnset

        return self._from_string(button.data_value)

    def update(self, data):
        if data is None:
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

class RadioButton(ProxyRadioButton):
    def __init__(self):
        #deprecationwarn(
        #    'RadioButton is deprecated, use ProxyRadioButton instead',
        #    stacklevel=3)
        ProxyRadioButton.__init__(self)
