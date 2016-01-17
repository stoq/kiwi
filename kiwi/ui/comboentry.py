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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""Widget for displaying a list of objects"""

import logging

import gtk
from gtk import gdk, keysyms

from kiwi.component import implements
from kiwi.enums import ComboColumn, ComboMode
from kiwi.interfaces import IEasyCombo
from kiwi.ui.popup import PopupWindow
from kiwi.ui.cellrenderer import ComboDetailsCellRenderer
from kiwi.ui.entry import KiwiEntry, ENTRY_MODE_DATA
from kiwi.ui.entrycompletion import KiwiEntryCompletion
from kiwi.utils import gsignal, type_register

log = logging.getLogger('kiwi.ui.combo')


class _ComboEntryPopup(PopupWindow):

    FRAME_PADDING = (0, 0, 0, 0)

    gsignal('text-selected', str)

    def __init__(self, comboentry):
        self._comboentry = comboentry

        super(_ComboEntryPopup, self).__init__(comboentry)

        # Number of visible rows in the popup window, sensible
        # default value from other toolkits
        self._visible_rows = 10
        self._initial_text = None
        self._filter_model = None

    def get_main_widget(self):
        vbox = gtk.VBox()
        vbox.show()

        self._sw = gtk.ScrolledWindow()
        self._sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        vbox.pack_start(self._sw)
        self._sw.show()

        self._model = gtk.ListStore(str)
        self._treeview = gtk.TreeView(self._model)
        self._treeview.set_enable_search(False)
        self._treeview.connect('motion-notify-event',
                               self._on_treeview__motion_notify_event)
        self._treeview.connect('button-release-event',
                               self._on_treeview__button_release_event)
        self._treeview.add_events(gdk.BUTTON_PRESS_MASK)
        self._selection = self._treeview.get_selection()
        self._selection.set_mode(gtk.SELECTION_BROWSE)
        self._renderer = ComboDetailsCellRenderer()
        self._treeview.append_column(
            gtk.TreeViewColumn('Foo', self._renderer,
                               label=0, data=1))
        self._treeview.set_headers_visible(False)
        self._sw.add(self._treeview)
        self._treeview.show()

        self._label = gtk.Label()

        return vbox

    def get_widget_for_popup(self):
        return self._comboentry.entry

    def popup(self, text=None, filter=False):
        """
        Shows the list of options. And optionally selects an item
        :param text: text to select
        :param filter: filter the list of options. A filter_model must be
        set using :class:`set_model`()
        """
        self.GRAB_WINDOW = not filter
        self.GRAB_ADD = not filter
        treeview = self._treeview

        if filter and self._filter_model:
            model = self._filter_model
        else:
            model = self._model

        if not len(model):
            return

        treeview.set_model(model)
        treeview.set_hover_expand(True)
        selection = treeview.get_selection()
        selection.unselect_all()
        if text:
            for row in model:
                if text in row:
                    selection.select_iter(row.iter)
                    treeview.scroll_to_cell(row.path, use_align=True,
                                            row_align=0.5)
                    treeview.set_cursor(row.path)
                    break

        popped = super(_ComboEntryPopup, self).popup()
        if not popped:
            return False

        treeview.set_size_request(-1, -1)
        if not filter:
            # Grab window
            self.grab_focus()
            if not self._treeview.has_focus():
                self._treeview.grab_focus()

        return True

    def set_label_text(self, text):
        if text is None:
            text = ''
            self._label.hide()
        else:
            self._label.show()
        self._label.set_text(text)

    def set_model(self, model):
        if isinstance(model, gtk.TreeModelFilter):
            self._filter_model = model
            model = model.get_model()

        self._treeview.set_model(model)
        self._model = model

    def confirm(self):
        model, treeiter = self._selection.get_selected()
        if treeiter:
            self.emit('text-selected', model[treeiter][0])

    def handle_key_press_event(self, event):
        if event.keyval == keysyms.Tab:
            self.popdown()
            # XXX: private member of comboentry
            self._comboentry._button.grab_focus()
            return True
        return False

    # Callbacks

    def _on_treeview__motion_notify_event(self, treeview, event):
        retval = treeview.get_path_at_pos(int(event.x),
                                          int(event.y))
        if not retval:
            return
        path, column, x, y = retval
        self._selection.select_path(path)
        self._treeview.set_cursor(path)

    def _on_treeview__button_release_event(self, treeview, event):
        retval = treeview.get_path_at_pos(int(event.x),
                                          int(event.y))
        if not retval:
            return
        path, column, x, y = retval

        model = treeview.get_model()
        self.emit('text-selected', model[path][0])

    def get_size(self, allocation, monitor):
        treeview = self._treeview
        treeview.realize()

        rows = len(self._treeview.get_model())
        if rows > self._visible_rows:
            rows = self._visible_rows
            self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        else:
            self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)

        cell_height = treeview.get_cell_area(0, treeview.get_column(0)).height
        height = cell_height * rows
        # Use half of the available screen space
        max_height = monitor.height / 2
        if height > max_height:
            height = int(max_height)
        elif height < 0:
            height = 0

        return allocation.width, height

    def get_selected_iter(self):
        model, treeiter = self._selection.get_selected()

        # if the model currently being used is a TreeModelFilter, convert
        # the iter to be a TreeModel iter (witch is what the user expects)
        if isinstance(model, gtk.TreeModelFilter) and treeiter:
            treeiter = model.convert_iter_to_child_iter(treeiter)
        return treeiter

    def set_selected_iter(self, treeiter):
        """
        Selects an item in the comboentry given a treeiter
        :param treeiter: the tree iter to select
        """
        model = self._treeview.get_model()

        # Since the user passed a TreeModel iter, if the model currently
        # being used is a TreeModelFilter, convert it to be a TreeModelFilter
        # iter
        if isinstance(model, gtk.TreeModelFilter):
            # See #3099 for an explanation why this is needed and a
            # testcase
            tmodel = model.get_model()
            if tmodel.iter_is_valid(treeiter):
                # revert back to the unfiltered model so we can select
                # the right object
                self._treeview.set_model(tmodel)
                self._selection = self._treeview.get_selection()
            else:
                treeiter = model.convert_child_iter_to_iter(treeiter)
        self._selection.select_iter(treeiter)

    def set_details_callback(self, callable):
        self._renderer.set_details_callback(callable)

type_register(_ComboEntryPopup)


class ComboEntry(gtk.VBox):

    implements(IEasyCombo)

    gsignal('changed')
    gsignal('activate')

    def __init__(self, entry=None):
        """
        Create a new ComboEntry object.
        :param entry: a gtk.Entry subclass to use
        """
        gtk.VBox.__init__(self)
        self._popping_down = False

        if not entry:
            entry = KiwiEntry()

        if isinstance(entry, KiwiEntry):
            entry.set_normal_completion()

        self.hbox = gtk.HBox()
        self.pack_start(gtk.EventBox())
        self.pack_start(self.hbox, expand=False)
        self.pack_start(gtk.EventBox())

        self.mode = ComboMode.UNKNOWN
        self.entry = entry
        self.entry.connect('activate',
                           self._on_entry__activate)
        self.entry.connect('changed',
                           self._on_entry__changed)
        self.entry.connect('scroll-event',
                           self._on_entry__scroll_event)
        self.entry.connect('key-press-event',
                           self._on_entry__key_press_event)
        self.entry.connect('focus-out-event',
                           self._on_entry__focus_out_event)

        self.hbox.pack_start(self.entry, True, True)
        self.hbox.show_all()

        self._button = gtk.ToggleButton()
        self._button.connect('scroll-event', self._on_entry__scroll_event)
        self._button.connect('toggled', self._on_button__toggled)
        self._button.set_focus_on_click(False)
        self.hbox.pack_end(self._button, False, False)
        self._button.show()

        arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
        self._button.add(arrow)
        arrow.show()

        self._popup = _ComboEntryPopup(self)
        self._popup.connect('text-selected', self._on_popup__text_selected)
        self._popup.connect('hide', self._on_popup__hide)
        self._popup.set_size_request(-1, 24)

        completion = KiwiEntryCompletion()
        completion.set_popup_window(self._popup)
        completion.set_treeview(self._popup._treeview)
        self.entry.set_completion(completion)
        self.set_model(completion.get_model())

    # Virtual methods

    def do_grab_focus(self):
        self.entry.grab_focus()

    # Callbacks
    def _on_entry__focus_out_event(self, widget, event):
        # The popup window should be hidden if the entry loses the focus,
        # unless we have a combo entry and the user clicked the toggle button
        # to show the popup window
        if not self._button.get_active():
            self.popdown()

    def _on_entry_completion__match_selected(self, completion, model, iter):
        # the iter we receive is specific to the tree model filter used
        # In the entry completion, convert it to an iter in the real model
        if isinstance(model, gtk.TreeModelFilter):
            iter = model.convert_iter_to_child_iter(iter)
        self.set_active_iter(iter)

    def _on_entry__activate(self, entry):
        self.emit('activate')

    def _on_entry__changed(self, entry):
        self._update_current_object()
        self.emit('changed')

    def _on_entry__scroll_event(self, entry, event):
        model = self.get_model()
        if not len(model):
            return
        treeiter = self._popup.get_selected_iter()
        # If nothing is selected, select the first one
        if not treeiter:
            self.set_active_iter(model[0].iter)
            return

        curr = model[treeiter].path[0]
        # Scroll up, select the previous item
        if event.direction == gdk.SCROLL_UP:
            curr -= 1
            if curr >= 0:
                self.set_active_iter(model[curr].iter)
        # Scroll down, select the next item
        elif event.direction == gdk.SCROLL_DOWN:
            curr += 1
            if curr < len(model):
                self.set_active_iter(model[curr].iter)

    def _on_entry__key_press_event(self, entry, event):
        """
        Mimics Combobox behavior

        Alt+Down: Open popup
        """
        keyval, state = event.keyval, event.state
        state &= gtk.accelerator_get_default_mod_mask()
        if ((keyval == keysyms.Down or keyval == keysyms.KP_Down) and
            state == gdk.MOD1_MASK):
            self.popup()
            return True

    def _on_popup__hide(self, popup):
        self._popping_down = True
        self._button.set_active(False)
        self._popping_down = False

    def _on_popup__text_selected(self, popup, text):
        self.set_text(text)
        self.popdown()
        self.entry.grab_focus()
        self.entry.set_position(len(self.entry.get_text()))
        self.emit('changed')

    def _on_button__toggled(self, button):
        if self._popping_down:
            return
        self.popup()

    # Private

    def _update_current_object(self):
        if self.entry.get_mode() != ENTRY_MODE_DATA:
            return

        completion = self.entry.get_completion()
        treeview = completion.get_treeview()
        selection = treeview.get_selection()
        current_object = self.entry.get_current_object()

        if current_object is None:
            selection.unselect_all()
            return

        model = treeview.get_model()
        treeiter = self.entry.get_iter_by_data(current_object)
        if treeiter and isinstance(model, gtk.TreeModelFilter):
            # Just like we do in comboentry.py, convert iter between
            # models. See #3099 for more information
            tmodel = model.get_model()
            if tmodel.iter_is_valid(treeiter):
                treeview.set_model(tmodel)
                selection = treeview.get_selection()
            else:
                treeiter = model.convert_child_iter_to_iter(treeiter)

        selection.select_iter(treeiter)

    def _update(self):
        model = self._model
        if not len(model):
            return

        iter = self._popup.get_selected_iter()
        if not iter:
            iter = model[0].iter
        self._popup.set_selected_iter(iter)

    # Public API

    def clicked(self):
        pass

    def popup(self):
        """
        Show the popup window
        """
        self._popup.popup(self.entry.get_text())

    def popdown(self):
        """
        Hide the popup window
        """
        self._popup.popdown()
        # FIXME: This is a very ugly hack. For some reason, data is not
        # set when typing or pressing enter on the completion. It only works
        # with the mouse (both clicking on completion and scrolling results).
        # Find out why this happens and remove the try/except bellow.
        try:
            self.select_item_by_label(self.entry.get_text())
        except KeyError:
            pass

    def set_text(self, text):
        """
        Sets the text.
        :param text:
        """
        self.entry.set_text(text)
        self.emit('changed')

    def get_text(self):
        """
        Gets the current text.
        :returns: the text.
        """
        return self.entry.get_text()

    def set_model(self, model):
        """
        Set the tree model to model
        :param model: new model
        :type model: gtk.TreeModel
        """
        self._model = model
        self._popup.set_model(model)
        completion = self.entry.get_completion()
        completion.connect('match-selected',
                           self._on_entry_completion__match_selected)
        completion.set_model(model)

        self._update()

    def get_model(self):
        """
        Gets our model.
        :returns: model
        :rtype: gtk.TreeModel
        """
        return self._model

    def set_active_iter(self, iter):
        """
        Set the iter selected.
        :param iter: iter to select
        :type iter: gtk.TreeIter
        """
        self._popup.set_selected_iter(iter)
        text = self._model[iter][0]
        if text is not None:
            self.set_text(text)

    def get_active_iter(self):
        """
        Gets the selected iter.
        :returns: iter selected.
        :rtype: gtk.TreeIter
        """
        return self._popup.get_selected_iter()

    def get_mode(self):
        return self.mode

    def set_label_text(self, text):
        self._popup.set_label_text(text)

    def set_active(self, rowno):
        self.set_active_iter(self._model[rowno].iter)

    def set_details_callback(self, callable):
        """Display some details as a second line on each entry

        :param callable: a callable that expects an object and returns a
                         string
        """
        self._popup.set_details_callback(callable)

    # IEasyCombo interface

    def clear(self):
        """Removes all items from list"""
        self._model.clear()
        self.entry.set_text("")

    def prefill(self, itemdata, sort=False):
        """
        See :class:`kiwi.interfaces.IEasyCombo.prefill`
        """
        if not itemdata:
            # If itemdata has no items, just clear
            self.clear()
            return

        self._model.clear()
        self.entry.prefill(itemdata, sort)
        self.mode = self.entry.get_mode()

    def select_item_by_data(self, data):
        """
        See :class:`kiwi.interfaces.IEasyCombo.select_item_by_data`
        """
        treeiter = self.entry.get_iter_by_data(data)
        self.set_active_iter(treeiter)

    def select_item_by_label(self, text):
        """
        See :class:`kiwi.interfaces.IEasyCombo.select_item_by_label`
        """
        treeiter = self.entry.get_iter_by_label(text)
        self.set_active_iter(treeiter)

    def select_item_by_position(self, position):
        """
        See :class:`kiwi.interfaces.IEasyCombo.select_item_by_position`
        """
        row = self._model[position]
        self.set_active_iter(row.iter)

    def get_selected(self):
        """
        See :class:`kiwi.interfaces.IEasyCombo.get_selected`
        """
        treeiter = self.get_active_iter()
        if treeiter:
            return self.entry.get_selected_by_iter(treeiter)

    def get_selected_label(self):
        """
        See :class:`kiwi.interfaces.IEasyCombo.get_selected_label`
        """
        treeiter = self.get_active_iter()
        if treeiter:
            return self.entry.get_selected_label(treeiter)

    def get_selected_data(self):
        """
        See :class:`kiwi.interfaces.IEasyCombo.get_selected_data`
        """
        treeiter = self.get_active_iter()
        if treeiter:
            return self.entry.get_selected_data(treeiter)

    def select(self, obj):
        """
        See :class:`kiwi.interfaces.IEasyCombo.select`
        """
        try:
            treeiter = self.entry.get_iter_from_obj(obj)
        except KeyError:
            log.warn("%s does not contain a %r object" % (
                self.__class__.__name__, obj))
            return
        self.set_active_iter(treeiter)

    def append_item(self, label, data=None):
        """
        See :class:`kiwi.interfaces.IEasyCombo.append_item`
        """
        if not isinstance(label, basestring):
            raise TypeError("label must be string, found %s" % label)

        if self.mode == ComboMode.UNKNOWN:
            if data is not None:
                self.mode = ComboMode.DATA
            else:
                self.mode = ComboMode.STRING

        model = self._model
        if self.mode == ComboMode.STRING:
            if data is not None:
                raise TypeError("data can not be specified in string mode")
            model.append((label, None))
        elif self.mode == ComboMode.DATA:
            if data is None:
                raise TypeError("data must be specified in string mode")
            model.append((label, data))
        else:
            raise AssertionError

    def get_model_strings(self):
        """
        See :class:`kiwi.interfaces.IEasyCombo.get_model_strings`
        """
        return [row[ComboColumn.LABEL] for row in self._model]

    def get_model_items(self):
        """
        See :class:`kiwi.interfaces.IEasyCombo.get_model_items`
        """
        if self.mode != ComboMode.DATA:
            raise TypeError("get_model_items can only be used in data mode")

        model = self._model
        items = {}
        for row in model:
            items[row[ComboColumn.LABEL]] = row[ComboColumn.DATA]

        return items

    # IconEntry

    def set_pixbuf(self, pixbuf):
        self.entry.set_pixbuf(pixbuf)

    def update_background(self, color):
        self.entry.update_background(color)

    def get_background(self):
        return self.entry.get_background()

type_register(ComboEntry)
