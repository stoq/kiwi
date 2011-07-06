#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
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

"""Reimplementation of GtkComboBoxEntry in Python.

The main difference between the L{BaseComboBoxEntry} and GtkComboBoxEntry
is that a {kiwi.ui.widgets.entry.Entry} is used instead of a GtkEntry."""

import gobject
import gtk

from kiwi.python import deprecationwarn
from kiwi.ui.entry import KiwiEntry

class BaseComboBoxEntry(gtk.ComboBox):
    def __init__(self, model=None, text_column=-1):
        deprecationwarn(
            'ComboBoxEntry is deprecated, use ComboEntry instead',
            stacklevel=3)

        gtk.ComboBox.__init__(self)
        self.entry = KiwiEntry()
        # HACK: We need to set a private variable, this seems to
        #       be the only way of doing so
        self.entry.start_editing(gtk.gdk.Event(gtk.gdk.BUTTON_PRESS))
        self.add(self.entry)
        self.entry.show()

        self._text_renderer = gtk.CellRendererText()
        self.pack_start(self._text_renderer, True)
        self.set_active(-1)
        self.entry_changed_id = self.entry.connect('changed',
                                                     self._on_entry__changed)
        self._active_changed_id = self.connect("changed",
                                               self._on_entry__active_changed)
        self._has_frame_changed(None)
        self.connect("notify::has-frame", self._has_frame_changed)

        if not model:
            model = gtk.ListStore(str)
            text_column = 0
        self.set_model(model)
        self.set_text_column(text_column)

    # Virtual methods
    def do_mnemnoic_activate(self, group_cycling):
        self.entry.grab_focus()
        return True

    def do_grab_focus(self):
        self.entry.grab_focus()

    # Signal handlers
    def _on_entry__active_changed(self, combobox):
        iter = combobox.get_active_iter()
        if not iter:
            return

        self.entry.handler_block(self.entry_changed_id)
        model = self.get_model()
        self.entry.set_text(model[iter][self._text_column])
        self.entry.handler_unblock(self.entry_changed_id)

    def _has_frame_changed(self, pspec):
        has_frame = self.get_property("has-frame")
        self.entry.set_has_frame(has_frame)

    def _on_entry__changed(self, entry):
        self.handler_block(self._active_changed_id)
        self.set_active(-1)
        self.handler_unblock(self._active_changed_id)

    # Public API
    def set_text_column(self, text_column):
        self._text_column = text_column
        if text_column != -1:
            self.set_attributes(self._text_renderer, text=text_column)

    def get_text_column(self):
        return self._text_column

    # IconEntry
    def set_pixbuf(self, pixbuf):
        self.entry.set_pixbuf(pixbuf)

    def update_background(self, color):
        self.entry.update_background(color)

    def get_background(self):
        return self.entry.get_background()

gobject.type_register(BaseComboBoxEntry)

def test():
    win = gtk.Window()
    win.connect('delete-event', gtk.main_quit)

    e = BaseComboBoxEntry()
    win.add(e)

    m = gtk.ListStore(str)
    m.append(['foo'])
    m.append(['bar'])
    m.append(['baz'])
    e.set_model(m)
    win.show_all()
    gtk.main()

if __name__ == '__main__':
    test()
