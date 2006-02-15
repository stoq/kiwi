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
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#            Gustavo Rahal <gustavo@async.com.br>
#            Daniel Saran R. da Cunha <daniel@async.com.br>
#            Evandro Vale Miquelito <evandro@async.com.br>
#

"""GtkComboBox and GtkComboBoxEntry support for the Kiwi Framework.

The GtkComboBox and GtkComboBoxEntry classes here are also slightly extended
they contain methods to easily insert and retrieve data from combos.
"""

import gobject
import gtk
from gtk import keysyms

from kiwi import ValueUnset
from kiwi.ui.comboboxentry import BaseComboBoxEntry
from kiwi.ui.comboentry import ComboEntry
from kiwi.ui.combomixin import COL_COMBO_LABEL, COMBO_MODE_STRING, \
     COMBO_MODE_DATA, COMBO_MODE_UNKNOWN, ComboMixin
from kiwi.ui.widgets.proxy import WidgetMixin, WidgetMixinSupportValidation
from kiwi.utils import PropertyObject, gproperty

class ProxyComboBox(PropertyObject, gtk.ComboBox, ComboMixin, WidgetMixin):

    __gtype_name__ = 'ProxyComboBox'

    def __init__(self):
        gtk.ComboBox.__init__(self)
        ComboMixin.__init__(self)
        WidgetMixin.__init__(self)
        PropertyObject.__init__(self)
        self.connect('changed', self._on__changed)

        renderer = gtk.CellRendererText()
        self.pack_start(renderer)
        self.add_attribute(renderer, 'text', COL_COMBO_LABEL)

    # GtkComboBox is a GtkContainer subclass which implements __len__ in
    # PyGTK in 2.8 and higher. Therefor we need to provide our own
    # implementation to be backwards compatible and override the new
    # behavior in 2.8
    def __len__(self):
        return len(self.get_model())

    def _on__changed(self, combo):
        self.emit('content-changed')

    def read(self):
        if self.mode == COMBO_MODE_STRING:
            return self._from_string(self.get_selected_label())
        elif self.mode == COMBO_MODE_DATA:
            return self.get_selected_data()

        return ValueUnset

    def update(self, data):
        # We dont need validation because the user always
        # choose a valid value

        if data is None:
            return
        elif self.mode == COMBO_MODE_STRING:
            self.select_item_by_label(self._as_string(data))
        elif self.mode == COMBO_MODE_DATA:
            self.select_item_by_data(data)
        else:
            # XXX: When setting the datatype to non string, automatically go to
            #      data mode
            raise TypeError("unknown ComboBox mode. Did you call prefill?")

    def prefill(self, itemdata, sort=False):
        ComboMixin.prefill(self, itemdata, sort)

        # we always have something selected, by default the first item
        self.set_active(0)
        self.emit('content-changed')

    def clear(self):
        ComboMixin.clear(self)
        self.emit('content-changed')

class ProxyComboBoxEntry(PropertyObject, BaseComboBoxEntry, ComboMixin,
                         WidgetMixinSupportValidation):
    __gtype_name__ = 'ProxyComboBoxEntry'
    # it doesn't make sense to connect to this signal
    # because we want to monitor the entry of the combo
    # not the combo box itself.

    gproperty("list-editable", bool, True, "Editable")

    def __init__(self, **kwargs):
        BaseComboBoxEntry.__init__(self)
        ComboMixin.__init__(self)
        WidgetMixinSupportValidation.__init__(self, widget=self.entry)
        PropertyObject.__init__(self, **kwargs)

        self.set_text_column(COL_COMBO_LABEL)
        # here we connect the expose-event signal directly to the entry
        self.child.connect('changed', self._on_child_entry__changed)

        # HACK! we force a queue_draw because when the window is first
        # displayed the icon is not drawn.
        gobject.idle_add(self.queue_draw)

        self.set_events(gtk.gdk.KEY_RELEASE_MASK)
        self.connect("key-release-event", self._on__key_release_event)

    def prop_set_list_editable(self, value):
        if self.mode == COMBO_MODE_DATA:
            return

        self.entry.set_editable(value)

        return value

    def _update_selection(self, text=None):
        if text is None:
            text = self.entry.get_text()

        self.select_item_by_label(text)

    def _add_text_to_combo_list(self):
        text = self.entry.get_text()
        if not text.strip():
            return

        if text in self.get_model_strings():
            return

        self.entry.set_text('')
        self.append_item(text)
        self._update_selection(text)

    def _on__key_release_event(self, widget, event):
        """Checks for "Enter" key presses and add the entry text to
        the combo list if the combo list is set as editable.
        """
        if not self.list_editable:
            return

        if event.keyval in (keysyms.KP_Enter,
                            keysyms.Return):
            self._add_text_to_combo_list()

    def _on_child_entry__changed(self, widget):
        """Called when something on the entry changes"""
        if not widget.get_text():
            return

        self.emit('content-changed')

    def set_mode(self, mode):
        # If we're in the transition to go from
        # unknown->label set editable to False
        if (self.mode == COMBO_MODE_UNKNOWN and mode == COMBO_MODE_DATA):
            self.entry.set_editable(False)

        ComboMixin.set_mode(self, mode)

    def read(self):
        mode = self.mode
        if mode == COMBO_MODE_STRING:
            return self.get_selected_label()
        elif mode == COMBO_MODE_DATA:
            return self.get_selected_data()
        else:
            return ValueUnset

    def before_validate(self, data):
        """ComboBoxEntry has a validate default handler that check if the
        text of the entry is an item of the list"""

        # XXX: Check so data is in list
        #items = self.get_model_items()
        #if data not in items.keys():
        #    raise ValidationError("Entered value not in list")

    def update(self, data):
        if data is ValueUnset or data is None:
            self.entry.set_text("")
        elif self.mode == COMBO_MODE_STRING:
            self.select_item_by_label(data)
        elif self.mode == COMBO_MODE_DATA:
            self.select_item_by_data(data)
        else:
            raise AssertionError

    def prefill(self, itemdata, sort=False, clear_entry=False):
        ComboMixin.prefill(self, itemdata, sort)
        if clear_entry:
            self.entry.set_text("")

        # setup the autocompletion
        auto = gtk.EntryCompletion()
        auto.set_model(self.get_model())
        auto.set_text_column(COL_COMBO_LABEL)
        self.entry.set_completion(auto)

    def clear(self):
        """Removes all items from list and erases entry"""
        ComboMixin.clear(self)
        self.entry.set_text("")

class ProxyComboEntry(PropertyObject, ComboEntry, ComboMixin, WidgetMixin):
    __gtype_name__ = 'ProxyComboEntry'

    def __init__(self):
        ComboEntry.__init__(self)
        ComboMixin.__init__(self)
        WidgetMixin.__init__(self)
        PropertyObject.__init__(self)

