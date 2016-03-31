#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005,2006,2008 Async Open Source
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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

import logging

import gtk

from kiwi.ui.hyperlink import HyperLink
from kiwi.ui.objectlist import ObjectList, ObjectTree
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.colorbutton import ProxyColorButton
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.radiobutton import ProxyRadioButton
from kiwi.ui.widgets.entry import ProxyEntry, ProxyDateEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.widgets.button import ProxyButton

# pyflakes
HyperLink
ObjectList
ObjectTree
ProxyLabel
ProxyComboEntry
ProxyComboBox
ProxyCheckButton
ProxyColorButton
ProxyRadioButton
ProxyEntry
ProxyDateEntry
ProxySpinButton
ProxyTextView
ProxyButton


log = logging.getLogger('builderloader')


class BuilderWidgetTree:
    def __init__(self, view, gladefile=None, domain=None, data=None):
        self._view = view
        self._gladefile = gladefile
        self._builder = gtk.Builder()

        if domain is not None:
            self._builder.set_translation_domain(domain)

        if gladefile is not None:
            self._builder.add_from_file(gladefile)
        elif data is not None:
            self._builder.add_from_string(data)
        else:
            raise ValueError("need a gladefile or data")

        self._attach_widgets()

    def _attach_widgets(self):
        # Attach widgets in the widgetlist to the view specified, so
        # widgets = [label1, button1] -> view.label1, view.button1

        for obj in self._builder.get_objects():
            if isinstance(obj, gtk.Buildable):
                object_name = gtk.Buildable.get_name(obj)
                setattr(self._view, object_name, obj)

    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        widget = self._builder.get_object(name)

        if widget is None:
            raise AttributeError(
                "Widget %s not found in view %s" % (name, self._view))
        return widget

    def get_widgets(self):
        return self._builder.get_objects()

    def get_sizegroups(self):
        return [obj for obj in self._builder.get_objects()
                if isinstance(obj, gtk.SizeGroup)]

    def signal_autoconnect(self, obj):
        self._builder.connect_signals(obj)
