#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2016 Async Open Source
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
# Author(s): Thiago Bellini <hackedbellini@async.com.br>
#

import gettext

from gi.repository import Gtk, GLib, GObject, Gdk, Pango, GdkPixbuf

from kiwi.ui.cellrenderer import ComboDetailsCellRenderer
from kiwi.ui.popup import PopupWindow
from kiwi.utils import gsignal, type_register

_ = lambda m: gettext.dgettext('kiwi', m)

_NO_ITEMS_MARKER = object()
(COL_LABEL,
 COL_DATA,
 COL_PIXBUF,
 COL_ATTACHED) = range(4)


class _MultiComboPopup(PopupWindow):

    MAX_VISIBLE_ROWS = 10

    gsignal('item-selected', object)

    def __init__(self, widget, model):
        self._combo_model = model
        self._model = model.filter_new()
        self._model.connect('row-inserted', self._on_model__row_inserted)
        self._model.connect('row-deleted', self._on_model__row_deleted)
        self._model.connect('row-changed', self._on_model__row_changed)

        super(_MultiComboPopup, self).__init__(widget)

    #
    #  EntryPopup
    #

    def confirm(self):
        self._activate_selected_item()

    def get_main_widget(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self._sw = Gtk.ScrolledWindow()
        self._sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        vbox.pack_start(self._sw, True, True, 0)

        self._treeview = Gtk.TreeView(self._model)
        self._treeview.connect('motion-notify-event',
                               self._on_treeview__motion_notify_event)
        self._treeview.connect('button-release-event',
                               self._on_treeview__button_release_event)
        self._treeview.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.KEY_PRESS_MASK)

        self._selection = self._treeview.get_selection()
        self._selection.set_mode(Gtk.SelectionMode.BROWSE)

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        self._treeview.append_column(
            Gtk.TreeViewColumn('', pixbuf_renderer, pixbuf=COL_PIXBUF))

        text_renderer = ComboDetailsCellRenderer()
        self._treeview.append_column(
            Gtk.TreeViewColumn('', text_renderer, label=COL_LABEL, data=COL_DATA))

        self._model.set_visible_func(
            lambda model, itr, data: not model[itr][COL_ATTACHED])

        self._treeview.set_headers_visible(False)
        self._sw.add(self._treeview)

        vbox.show_all()
        return vbox

    def get_widget_for_popup(self):
        # FIXME: self.widget should work, but for some reason it is making
        # the popup calculation for the position be wrong.
        # Because of that we are getting the widget's allocation om get_size
        return self.attached_widget.textview

    def get_size(self, allocation, monitor):
        # FIXME: We should use the provided allocation, but it is not the one
        # we want. See the comment on get_widget_for_popup for more details
        allocation = self.attached_widget.get_allocation()
        self._treeview.realize()

        rows = len(self._treeview.get_model())
        if rows > self.MAX_VISIBLE_ROWS:
            rows = self.MAX_VISIBLE_ROWS
            self._sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        else:
            self._sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)

        cell_area = self._treeview.get_background_area(
            Gtk.TreePath(0), self._treeview.get_column(0))
        cell_height = cell_area.height
        # Use half of the available screen space
        height = min(max(cell_height * rows, cell_height), monitor.height / 2)
        height += self.FRAME_PADDING[0] + self.FRAME_PADDING[1]

        self._treeview.set_size_request(-1, -1)
        return allocation.width, height

    def popup(self):
        super(_MultiComboPopup, self).popup()
        self.attached_widget.dropbutton.set_property('active', True)

    def popdown(self):
        super(_MultiComboPopup, self).popdown()
        self.attached_widget.dropbutton.set_property('active', False)

    #
    #  Private
    #

    def _resize(self):
        widget = self.attached_widget
        allocation = widget.get_allocation()
        screen = widget.get_screen()
        window = widget.get_window()
        # FIXME: window will be None on a test, but it is hard to tell which
        # one since it breaks one randomly because of the idle_add.
        if window is not None:
            monitor_num = screen.get_monitor_at_window(widget.get_window())
        else:
            monitor_num = 0
        monitor = screen.get_monitor_geometry(monitor_num)

        self.set_size_request(*self.get_size(allocation, monitor))

    def _select_path_for_event(self, event):
        path = self._treeview.get_path_at_pos(int(event.x), int(event.y))
        if not path:
            return

        path, column, x, y = path
        self._selection.select_path(path)
        self._treeview.set_cursor(path)

    def _activate_selected_item(self):
        model, treeiter = self._selection.get_selected()
        if treeiter:
            itr = model.convert_iter_to_child_iter(treeiter)
            self.emit('item-selected', self._combo_model[itr])

    def _update_ui(self):
        self._treeview.set_sensitive(self.attached_widget.has_items_to_select())
        GLib.idle_add(self._resize)

    #
    #  Callbacks
    #

    def _on_model__row_changed(self, model, path, itr):
        self._update_ui()

    def _on_model__row_inserted(self, model, path, itr):
        self._update_ui()

    def _on_model__row_deleted(self, model, path):
        self._update_ui()

    def _on_treeview__motion_notify_event(self, treeview, event):
        self._select_path_for_event(event)

    def _on_treeview__button_release_event(self, treeview, event):
        self._select_path_for_event(event)
        self._activate_selected_item()


class _MultiComboCloseButton(Gtk.Button):

    __gtype_name__ = 'MultiComboCloseButton'

    def __init__(self, **kwargs):
        super(_MultiComboCloseButton, self).__init__(**kwargs)

        self.set_relief(Gtk.ReliefStyle.NONE)
        image = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        self.add(image)


type_register(_MultiComboCloseButton)


class MultiCombo(Gtk.Box):
    """Multi selection combo.

    Just like a combo entry, but allows multiple items to be selected
    at the same time.

    Inspired by react-select::

        http://jedwatson.github.io/react-select/

    """

    gsignal('item-added', object)
    gsignal('item-removed', object)

    width = GObject.Property(type=int, default=200)
    max_label_chars = GObject.Property(type=int, default=50)
    scrolling_threshold = GObject.Property(type=int, default=3)

    def __init__(self, **kwargs):
        super(MultiCombo, self).__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)

        self.model = Gtk.ListStore(str, object, GdkPixbuf.Pixbuf, object)
        self._row_height = None
        self._setup_ui()

        self.popup = _MultiComboPopup(self, self.model)
        self.popup.connect('item-selected', self._on_popup__item_selected)

        self.set_size_request(self.width, -1)

        self.connect('notify::width', self._on__notify_width)
        self.connect('notify::scrolling_threshold',
                     self._on__notify_scrolling_threshold)

    #
    #  Public API
    #

    def prefill(self, items):
        """Prefill items for selection.

        :param items: a sequence of tuples containing: (label, data) or
            even (label, data, pixbuf) if one wants to display a pixbuf
            next to the label
        """
        self.model.clear()
        inserted = {}

        for item in items:
            if len(item) == 3:
                label, data, pixbuf = item
            elif len(item) == 2:
                label, data = item
                pixbuf = None
            else:
                raise AssertionError

            count = inserted.setdefault(label, 0)
            inserted[label] += 1
            if count:
                label += ' (%d)' % (count, )

            self.model.append((label, data, pixbuf, None))

        self.model.append(
            (_("No items to select..."), _NO_ITEMS_MARKER, None,
             self.has_items_to_select()))

    def clear(self):
        """Unselect everything that is currently selected."""
        for item in self._items:
            self.remove_selection(item)

    def has_items_to_select(self):
        """Check weather we have items visible for selection or not."""
        return any(not item[COL_ATTACHED] for item in self.model
                   if item[COL_DATA] is not _NO_ITEMS_MARKER)

    def get_iter_by_data(self, data):
        """Get an iter referencing the given data.

        :param data: the data used for prefilling the row
        :returns: the `Gtk.TreeIter` referencing that row
        """
        for row in self.model:
            if row[COL_DATA] == data:
                return row.iter
        else:
            raise KeyError(
                "No item correspond to data %r in the combo %s" % (data, self))

    def get_iter_by_label(self, label):
        """Get an iter referencing the given label.

        :param label: the label used for prefilling the row
        :returns: the `Gtk.TreeIter` referencing that row
        """
        for row in self.model:
            if row[COL_LABEL] == label:
                return row.iter
        else:
            raise KeyError(
                "No item correspond to label %r in the combo %s" % (label, self))

    def add_selection_by_data(self, data):
        """Add a selection using the given data.

        :param data: the data that will be selected. Note that
            it should have been prefilled before using the
            :meth:`.prefill` method.
        """
        self._add_selection(self.get_iter_by_data(data))

    def add_selection_by_label(self, label):
        """Add a selection using the given label.

        :param label: the label that will be selected. Note that
            it should have been prefilled before using the
            :meth:`.prefill` method.
        """
        self._add_selection(self.get_iter_by_label(label))

    def remove_selection_by_data(self, data):
        """Remove a selection using the given data.

        :param data: the data that will removed from the selection.
        """
        self._remove_selection(self.get_iter_by_data(data))

    def remove_selection_by_label(self, label):
        """Remove a selection using the given label.

        :param label: the label that will removed from the selection.
        """
        self._remove_selection(self.get_iter_by_label(label))

    def get_selection_label(self):
        """Get the current selection label.

        :returns: a `set` containing the selected labels
        """
        return set(row[COL_LABEL] for row in self._get_selected_rows())

    def get_selection_data(self):
        """Get the current selection data.

        :returns: a `set` containing the selected data
        """
        return set(row[COL_DATA] for row in self._get_selected_rows())

    #
    #  Private
    #

    def _get_selected_rows(self):
        return (row for row in self.model
                if row[COL_ATTACHED] and row[COL_DATA] is not _NO_ITEMS_MARKER)

    def _add_selection(self, row):
        assert row[COL_ATTACHED] is None

        itr = self.textbuffer.get_end_iter()
        anchor = self.textbuffer.create_child_anchor(itr)
        widget = self._get_item_widget(row)
        self.textview.add_child_at_anchor(widget, anchor)

        self.model.set_value(row.iter, COL_ATTACHED, anchor)
        self.emit('item-added', row[COL_DATA])

        self._update_no_items_marker()
        # Acording to the documentation, PRIORITY_HIGH_IDLE + 20 is
        # used by redrawing operations so PRIORITY_HIGH_IDLE + 25
        # should be enought to make sure we call callback just after
        # the widget finishes redrawing itself.
        GLib.timeout_add(100, self._scroll_to_item, row,
                         priority=GLib.PRIORITY_HIGH_IDLE + 25)

    def _remove_selection(self, row):
        assert row[COL_ATTACHED] is not None

        start_itr = self.textbuffer.get_iter_at_child_anchor(row[COL_ATTACHED])
        end_itr = start_itr.copy()
        end_itr.forward_char()
        self.textbuffer.delete(start_itr, end_itr)

        self.model.set_value(row.iter, COL_ATTACHED, None)
        self.emit('item-removed', row[COL_DATA])

        self._update_no_items_marker()

    def _get_item_widget(self, row):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        button = _MultiComboCloseButton()
        button.connect('clicked', self._on_remove_button__clicked, row)
        hbox.add(button)

        pixbuf = row[COL_PIXBUF]
        if pixbuf is not None:
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            hbox.add(img)

        label = Gtk.Label()
        label.set_padding(2, 0)
        text = str(row[COL_LABEL])
        # For some reason, if we don't set the width-chars here it will
        # ellipsize the full string.
        label.set_width_chars(min(len(text), self.max_label_chars))
        label.set_max_width_chars(self.max_label_chars)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        markup = '<u>%s</u>' % (GLib.markup_escape_text(text), )
        label.set_tooltip_markup(markup)
        label.set_markup(markup)
        hbox.add(label)

        hbox.show_all()
        return hbox

    def _setup_ui(self):
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                        Gtk.PolicyType.NEVER)
        self.pack_start(self.scrolled_window, True, True, 0)

        self.textbuffer = Gtk.TextBuffer()
        self.textbuffer.connect('changed', self._on_textbuffer__changed)
        self.textview = Gtk.TextView.new_with_buffer(self.textbuffer)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.scrolled_window.add(self.textview)

        self.dropbutton = Gtk.ToggleButton()
        self.dropbutton.add(Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT))
        self.dropbutton.connect('clicked', self._on_dropbbutton__toggled)
        self.pack_start(self.dropbutton, False, True, 0)

    def _adjust_size(self):
        itr = self.textbuffer.get_end_iter()
        line_range = self.textview.get_line_yrange(itr)
        if self._row_height is None:
            self._row_height = line_range[1] or None
            line_count = 0
        else:
            line_count = line_range[1] / self._row_height

        if line_count > self.scrolling_threshold:
            self.scrolled_window.set_property('vscrollbar-policy',
                                              Gtk.PolicyType.AUTOMATIC)
            self.set_size_request(
                self.width,
                self._row_height * self.scrolling_threshold)
        else:
            self.scrolled_window.set_property('vscrollbar-policy',
                                              Gtk.PolicyType.NEVER)
            self.set_size_request(self.width, -1)

        if self.popup.visible:
            # Acording to the documentation, PRIORITY_HIGH_IDLE + 20 is
            # used by redrawing operations so PRIORITY_HIGH_IDLE + 25
            # should be enought to make sure we call callback just after
            # the widget finishes redrawing itself.
            GLib.timeout_add(50, self.popup.adjust_position,
                             priority=GLib.PRIORITY_HIGH_IDLE + 25)

    def _update_no_items_marker(self):
        itr = self.get_iter_by_data(_NO_ITEMS_MARKER)
        self.model[itr][COL_ATTACHED] = self.has_items_to_select()

    def _scroll_to_item(self, item):
        itr = self.textbuffer.get_iter_at_child_anchor(item[COL_ATTACHED])
        itr.forward_char()
        self.textview.scroll_to_iter(itr, 0.0, False, 0.5, 0.5)

    #
    #  Callbacks
    #

    def _on__notify_width(self, widget, pspec):
        self._adjust_size()

    def _on__notify_scrolling_threshold(self, widget, pspec):
        self._adjust_size()

    def _on_textbuffer__changed(self, textbuffer):
        GLib.idle_add(self._adjust_size)

    def _on_dropbbutton__toggled(self, button):
        if button.get_active():
            self.popup.popup()
        else:
            self.popup.popdown()

    def _on_remove_button__clicked(self, button, row):
        self._remove_selection(row)

    def _on_popup__item_selected(self, popup, row):
        self._add_selection(row)
        # Popdown after the user has selected everything. It is the
        # only option he will have anyway
        if not self.has_items_to_select():
            self.popup.popdown()


type_register(MultiCombo)


if __name__ == '__main__':
    win = Gtk.Window()
    win.set_title('MultiCombo test')
    win.connect('delete-event', lambda w, e: Gtk.main_quit())
    win.set_size_request(-1, -1)

    widget = MultiCombo()
    win.add(widget)
    win.show_all()

    widget.prefill([
        ('Caramel', object()),
        ('Chocolate', object()),
        ('Cookies and Cream', object()),
        ('Peppermint', object()),
        ('Strawberry', object()),
        ('Vanilla', object()),
    ])

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
