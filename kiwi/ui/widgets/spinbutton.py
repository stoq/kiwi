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

"""GtkSpinButton support for the Kiwi Framework

L{SpinButton} is also enhanced to display an icon using
L{kiwi.ui.icon.IconEntry}
"""

import gtk

from kiwi.datatypes import number
from kiwi.python import deprecationwarn
from kiwi.ui.icon import IconEntry
from kiwi.ui.proxywidget import ValidatableProxyWidgetMixin
from kiwi.utils import PropertyObject, gsignal, type_register

class ProxySpinButton(PropertyObject, gtk.SpinButton, ValidatableProxyWidgetMixin):
    """
    A SpinButton subclass which adds supports for the Kiwi Framework.
    This widget supports validation
    The only allowed types for spinbutton are int and float.

    """
    __gtype_name__ = 'ProxySpinButton'
    allowed_data_types = number

    def __init__(self):
        # since the default data_type is str we need to set it to int
        # or float for spinbuttons
        gtk.SpinButton.__init__(self)
        PropertyObject.__init__(self, data_type=int)
        ValidatableProxyWidgetMixin.__init__(self)
        self._icon = IconEntry(self)
        self.set_property('xalign', 1.0)

    gsignal('changed', 'override')
    def do_changed(self):
        """Called when the content of the spinbutton changes.
        """
        # This is a work around, because GtkEditable.changed is called too
        # often, as reported here: http://bugzilla.gnome.org/show_bug.cgi?id=64998
        if self.get_text() != '':
            self.emit('content-changed')
            self.chain()

    def read(self):
        return self._from_string(self.get_text())

    def update(self, data):
        if data is None:
            self.set_text("")
        else:
            # set_value accepts a float or int, no as_string conversion needed,
            # and since we accept only int and float just send it in.
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

    def set_tooltip(self, text):
        self._icon.set_tooltip(text)

    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)

    def update_background(self, color):
        self._icon.update_background(color)

    def get_icon_window(self):
        return self._icon.get_icon_window()

class SpinButton(ProxySpinButton):
    def __init__(self):
        deprecationwarn(
            'SpinButton is deprecated, use ProxySpinButton instead',
            stacklevel=3)
        ProxySpinButton.__init__(self)
type_register(SpinButton)
