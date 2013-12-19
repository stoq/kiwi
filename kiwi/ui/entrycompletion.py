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
# Author(s): Ronaldo Maia <romaia@async.com.br>
#

import gobject
import gtk
from gtk import gdk
from gtk import keysyms

from kiwi.python import strip_accents
from kiwi.utils import gsignal, type_register

COMPLETION_TIMEOUT = 300
PAGE_INCREMENT = 14


class KiwiEntryCompletion(gtk.EntryCompletion):
    def __init__(self):
        gtk.EntryCompletion.__init__(self)

        self._inline_completion = False
        self._popup_completion = True
        self._entry = None
        self._completion_timeout = -1
        self._match_function = None
        self._match_function_data = None
        self._key = None
        self.changed_id = 0

        self._filter_model = None
        self._treeview = None

        self._popup_window = None
        self._selected_index = -1

    gsignal('match-selected', 'override')

    def do_match_selected(self, model, iter):
        self._entry.set_text(model[iter][0])
        return True

    def _visible_function(self, model, iter, data=None):
        if not self._entry:
            return False

        if not self._key:
            return False

        if self._match_function:
            return self._match_function(self, self._key, iter)

        value = model[iter][0]
        if not value:
            return False

        entry_text = self._entry.get_text()
        if self._entry.completion_ignore_case:
            entry_text = entry_text.lower()
            value = value.lower()
        if self._entry.completion_ignore_accents:
            entry_text = strip_accents(entry_text)
            value = strip_accents(value)

        return value.startswith(entry_text)

    def _connect_completion_signals(self):
        if self._popup_completion:
            self.changed_id = self._entry.connect('changed',
                                                  self._on_completion_changed)

            self._entry.connect('key-press-event',
                                self._on_completion_key_press)

            self._entry.connect('button-press-event', self._on_button_press_event)

    def _on_button_press_event(self, window, event):
        # If we're clicking outside of the window, close the popup
        if not self._popup_window:
            return

        if (event.window != self._popup_window.get_window() or
            (tuple(self._popup_window.allocation.intersect(
                   gdk.Rectangle(x=int(event.x), y=int(event.y),
                                 width=1, height=1)))) == (0, 0, 0, 0)):
            self.popdown()

    def _on_completion_timeout(self):
        minimum_key_length = self.get_property('minimum-key-length')
        if (self._filter_model and
            len(self._entry.get_text()) >= minimum_key_length and
            self._entry.is_focus()):
            self.complete()
            matches = self._filter_model.iter_n_children(None)
            if matches:
                self.popup()

        return False

    def _on_completion_changed(self, entry):
        if (self.get_property('minimum_key_length') > 0 and
            not self._entry.get_text()):
            self.popdown()
            return

        self._selected_index = -1

        if self._completion_timeout != -1:
            gobject.source_remove(self._completion_timeout)

        timeout = gobject.timeout_add(COMPLETION_TIMEOUT,
                                      self._on_completion_timeout)
        self._completion_timeout = timeout
        return True

    def _select_item(self, index):
        # Make the selection
        matches = self._filter_model.iter_n_children(None)

        if 0 <= index < matches:
            self._treeview.set_cursor((index,))
        else:
            selection = self._treeview.get_selection()
            selection.unselect_all()

        self._selected_index = index

    def _on_completion_key_press(self, entry, event):
        window = self._popup_window
        if window and not window.flags() & gtk.VISIBLE:
            return False

        if not self._treeview:
            return False

        matches = self._filter_model.iter_n_children(None)
        keyval = event.keyval
        index = self._selected_index

        if keyval == keysyms.Up or keyval == keysyms.KP_Up:
            index -= 1
            if index < -1:
                index = matches - 1

            self._select_item(index)
            return True

        elif keyval == keysyms.Down or keyval == keysyms.KP_Down:
            index += 1
            if index > matches - 1:
                index = -1

            self._select_item(index)
            return True

        elif keyval == keysyms.Page_Up:
            if index < 0:
                index = matches - 1
            elif index > 0 and index - PAGE_INCREMENT < 0:
                index = 0
            else:
                index -= PAGE_INCREMENT

            if index < 0:
                index = -1

            self._select_item(index)
            return True

        elif keyval == keysyms.Page_Down:
            if index < 0:
                index = 0
            elif index < matches - 1 and index + PAGE_INCREMENT > matches - 1:
                index = matches - 1
            else:
                index += PAGE_INCREMENT

            if index > matches:
                index = -1

            self._select_item(index)
            return True

        elif keyval == keysyms.Escape:
            self.popdown()
            return True

        elif (keyval == keysyms.Return or
              keyval == keysyms.KP_Enter):
            self.popdown()
            selection = self._treeview.get_selection()
            model, titer = selection.get_selected()
            if not titer:
                return False

            self._entry.handler_block(self.changed_id)
            self.emit('match-selected', model, titer)
            self._entry.handler_unblock(self.changed_id)
            selection.unselect_all()
            return True

        return False

    def _popup_grab_window(self):
        activate_time = 0L
        window = self._entry.get_window()
        if gdk.pointer_grab(window, True,
                            (gdk.BUTTON_PRESS_MASK |
                             gdk.BUTTON_RELEASE_MASK |
                             gdk.POINTER_MOTION_MASK),
                            None, None, activate_time) == 0:
            if gdk.keyboard_grab(window, True, activate_time) == 0:
                return True
            else:
                window.get_display().pointer_ungrab(activate_time)
                return False
        return False

    def _popup_ungrab_window(self):
        activate_time = 0L
        display = self._entry.get_window().get_display()
        display.pointer_ungrab(activate_time)
        display.keyboard_ungrab(activate_time)

    # Public API
    def complete(self):
        if not self._filter_model:
            return

        self._key = self._entry.get_text()
        self._filter_model.refilter()
        self._treeview.set_model(self._filter_model)
        if self._treeview.flags() & gtk.REALIZED:
            self._treeview.scroll_to_point(0, 0)

    def set_entry(self, entry):
        self._entry = entry
        self._connect_completion_signals()

    def get_entry(self):
        return self._entry

    def set_popup_window(self, window):
        self._popup_window = window

    def set_treeview(self, treeview):
        self._treeview = treeview

    def get_treeview(self):
        return self._treeview

    def popup(self):
        if not self._popup_window:
            return

        self._popup_window.popup(text=None, filter=True)
        self._popup_grab_window()

    def popdown(self):
        if not self._popup_window:
            return

        self._popup_window.popdown()
        self._popup_ungrab_window()

    def set_model(self, model):
        if not model:
            if self._popup_window:
                self._popup_window.set_model(None)
            self.popdown()
            self._model = None
            self._filter_model = None
            return

        self._model = model
        self._filter_model = model.filter_new()
        self._filter_model.set_visible_func(self._visible_function)
        if self._popup_window:
            self._popup_window.set_model(self._filter_model)

    def get_model(self):
        return self._model

    def set_match_func(self, function, data=None):
        self._match_function = function
        self._match_function_data = data

type_register(KiwiEntryCompletion)
