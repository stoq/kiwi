#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006 Async Open Source
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
# Author(s): Ali Afshar <aafshar@gmail.com>
#


"""Filechooser widgets for the kiwi framework"""

from gi.repository import Gtk, GObject

from kiwi.ui.proxywidget import ProxyWidgetMixin


class ProxyFileChooserWidget(Gtk.FileChooserWidget, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyFileChooserWidget'
    allowed_data_types = (str, )

    def __init__(self, action=Gtk.FileChooserAction.OPEN, backend=None):
        """
        Create a new ProxyFileChooserWidget object.
        :param action:
        :param backend:
        """
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = str
        Gtk.FileChooserWidget.__init__(self, action=action, backend=backend)

    def do_selection_changed(self):
        self.emit('content-changed')

    def read(self):
        return self.get_filename()

    def update(self, data):
        if data is None:
            return
        self.set_filename(data)


class ProxyFileChooserButton(Gtk.FileChooserButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyFileChooserButton'
    allowed_data_types = (str, )

    def __init__(self, title=None, backend=None, dialog=None):
        """
        Create a new ProxyFileChooserButton object.
        :param title:
        :param backend:
        :param dialog:
        """
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = str
        Gtk.FileChooserWidget.__init__(
            self, title=title, action=backend, dialog=dialog)

    def do_selection_changed(self):
        self.emit('content-changed')

    def read(self):
        return self.get_filename()

    def update(self, data):
        if data is None:
            return
        self.set_filename(data)

GObject.type_register(ProxyFileChooserButton)
