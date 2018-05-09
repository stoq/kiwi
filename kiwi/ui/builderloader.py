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
import platform
import tempfile

from gi.repository import Gtk

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


def _fix_widget(widget):
    # FIXME: There's a bug in GtkTable in versions before 3.22
    # that was making it expand in some ocasions that it shouldn't.
    # We should actually migrate to GtkGrid because GtkTable is deprecated
    # and will be removed in gtk4.
    # More info at: https://bugzilla.gnome.org/show_bug.cgi?id=769162
    if isinstance(widget, Gtk.Table):
        if not widget.get_vexpand_set():
            widget.set_vexpand_set(True)
            widget.set_vexpand(False)
        if not widget.get_hexpand_set():
            widget.set_hexpand_set(True)
            widget.set_hexpand(False)

    # FIXME: The overlay scrolling when a TextView is inside a ScrolledWindow
    # is somewhat broken in a way that it would make it get a height of 0 when
    # being displayed. This happens even in the glade so it is probably a gtk
    # issue. For now lets disable them until we find a better solution
    if isinstance(widget, Gtk.ScrolledWindow):
        widget.set_property('overlay_scrolling', False)

    return widget


class BuilderWidgetTree:
    def __init__(self, view, gladefile=None, domain=None, data=None):
        self._view = view
        self._gladefile = gladefile
        self._builder = Gtk.Builder()

        if domain is not None:
            self._builder.set_translation_domain(domain)

        if platform.system() == 'Windows' and gladefile:
            # Windows with python3 and Gtk3/pygi has this really nasty bug that
            # translations are actually working, but somehow the enconding is
            # messed up by Gtk. This might be fixed in newer versions of
            # Gtk/pygi, but currently, we are stuck with 3.24 on Windows. Other
            # References from a user with the same issue
            # https://stackoverflow.com/questions/32037573/
            # https://sourceforge.net/p/pygobjectwin32/tickets/22/
            # https://bugzilla.gnome.org/show_bug.cgi?id=753991
            # And the source of the workaround
            # https://github.com/tobias47n9e/pygobject-locale/issues/1#issuecomment-222287650
            import xml.etree.ElementTree as ET
            import gettext
            tree = ET.parse(gladefile)
            for node in tree.iter():
                if 'translatable' in node.attrib:
                    del node.attrib['translatable']
                    node.text = gettext.dgettext(domain, node.text)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tree.write(tmp, encoding='utf-8', xml_declaration=True)
            self._builder.add_from_file(tmp.name)
        elif gladefile is not None:
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
            if isinstance(obj, Gtk.Buildable):
                object_name = Gtk.Buildable.get_name(obj)
                setattr(self._view, object_name, _fix_widget(obj))

    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        widget = self._builder.get_object(name)

        if widget is None:
            raise AttributeError(
                "Widget %s not found in view %s" % (name, self._view))
        return _fix_widget(widget)

    def get_widgets(self):
        return [_fix_widget(w) for w in self._builder.get_objects()]

    def get_sizegroups(self):
        return [obj for obj in self.get_widgets()
                if isinstance(obj, Gtk.SizeGroup)]

    def signal_autoconnect(self, obj):
        self._builder.connect_signals(obj)
