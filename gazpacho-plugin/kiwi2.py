# Copyright (C) 2005 by Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

from datetime import date
from gettext import gettext as _

import gtk

from gazpacho.custompropertyeditor import CustomPropertyEditor
from gazpacho.util import get_bool_from_string_with_default
from gazpacho.widget import Widget

from kiwi.ui.widgets.checkbutton import CheckButton
from kiwi.ui.widgets.combobox import ComboBox, ComboBoxEntry
from kiwi.ui.widgets.entry import Entry
from kiwi.ui.widgets.label import Label
from kiwi.ui.widgets.list import List
from kiwi.ui.widgets.radiobutton import RadioButton
from kiwi.ui.widgets.spinbutton import SpinButton
from kiwi.ui.widgets.textview import TextView

root_library = 'kiwi.ui.widgets'
widget_prefix = 'Kiwi'

class DataTypeAdaptor(object):
    def create_editor(self, context):
        model = gtk.ListStore(str, object)
        model.append((_('String'), str))
        model.append((_('Integer'), int))
        model.append((_('Float'), float))
        model.append((_('Boolean'), bool))
        model.append((_('Date'), date))
        model.append((_('Object'), object))
        combo = gtk.ComboBox(model)
        renderer = gtk.CellRendererText()
        combo.pack_start(renderer)
        combo.add_attribute(renderer, 'text', 0)
        combo.set_active(0)
        combo.set_data('connection-id', -1)
        return combo        
    
    def update_editor(self, context, combo, kiwiwidget, proxy):
        connection_id = combo.get_data('connection-id')
        if (connection_id != -1):
            combo.disconnect(connection_id)
        connection_id = combo.connect('changed', self._editor_edit, kiwiwidget,
                                      proxy, context)
        combo.set_data('connection-id', connection_id)
        model = combo.get_model()
        value = kiwiwidget.get_property('data-type')
        for row in model:
            if row[1] == value:
                combo.set_active_iter(row.iter)
                break
            
    def _editor_edit(self, combo, kiwilist, proxy, context):
        model = combo.get_model()
        active_iter = combo.get_active_iter()
        value = model.get_value(active_iter, 1)
        proxy.set_value(value)

    def save(self, context, widget):
        gwidget = Widget.from_widget(widget)
        data_type = gwidget.get_glade_property('data-type')
        # data type is one of (str, float, int, bool)
        return data_type._value.__name__

class SpinBtnDataTypeAdaptor(DataTypeAdaptor):
    def create_editor(self, context):
        model = gtk.ListStore(str, object)
        model.append((_('Integer'), int))
        model.append((_('Float'), float))
        combo = gtk.ComboBox(model)
        renderer = gtk.CellRendererText()
        combo.pack_start(renderer)
        combo.add_attribute(renderer, 'text', 0)
        combo.set_active(0)
        combo.set_data('connection-id', -1)
        return combo

class ColumnDefinitionsAdaptor(object):
    def __init__(self):
        self._editor = ListColumnDefinitionsEditor()

    def set(self, context, kiwilist, value):
        kiwilist.set_property('column-definitions', value)

    def create_editor(self, context):
        button = gtk.Button(_('Edit...'))
        button.set_data('connection-id', -1)
        return button

    def update_editor(self, context, button, kiwilist, proxy):
        connection_id = button.get_data('connection-id')
        if connection_id != -1:
            button.disconnect(connection_id)
        connection_id = button.connect('clicked', self._editor_edit, kiwilist,
                                       proxy, context)
        button.set_data('connection-id', connection_id)

    def _editor_edit(self, button, kiwilist, proxy, context):
        application_window = context.get_application_window()
        self._editor.set_transient_for(application_window)
        self._editor.set_widget(kiwilist, proxy)
        self._editor.present()

(ATTRIBUTE,
 TITLE,
 DATA_TYPE,
 VISIBLE,
 JUSTIFY,
 TOOLTIP,
 FORMAT,
 WIDTH,
 SORTED,
 ORDER) = range(10)

class ListColumnDefinitionsEditor(CustomPropertyEditor):
    """This dialog is used to edit the column definitions of a Kiwi List"""

    def __init__(self):
        CustomPropertyEditor.__init__(self)

    def set_widget(self, widget, proxy):
        super(ListColumnDefinitionsEditor, self).set_widget(widget, proxy)
        self.set_title((_('Editing columns of list %s') % self.gwidget.name))
        self._load_columns()

    def _create_widgets(self):
        h_button_box = gtk.HButtonBox()
        h_button_box.set_layout(gtk.BUTTONBOX_START)
        self.add = gtk.Button(stock=gtk.STOCK_ADD)
        self.add.connect('clicked', self._on_add_clicked)
        h_button_box.pack_start(self.add)
        self.remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove.connect('clicked', self._on_remove_clicked)
        h_button_box.pack_start(self.remove)
        self.up = gtk.Button(stock=gtk.STOCK_GO_UP)
        self.up.connect('clicked', self._on_up_clicked)
        h_button_box.pack_start(self.up)
        self.down = gtk.Button(stock=gtk.STOCK_GO_DOWN)
        self.down.connect('clicked', self._on_down_clicked)
        h_button_box.pack_start(self.down)
        self.vbox.pack_start(h_button_box, False, False)
        self.model = gtk.ListStore(str, str, str, bool, str, str, str, int,
                                   bool, str)
        self.treeview = gtk.TreeView(self.model)
        self.treeview.set_size_request(580, 300)
        selection = self.treeview.get_selection()
        selection.connect('changed', self._on_selection__changed)
        for i, title in enumerate(('Attribute',
                                      'Title',
                                      'Data type')):
            self.treeview.append_column(self._create_text_column(title, i))

        self.treeview.append_column(self._create_bool_column('Visible', 3))
        for i, title in enumerate(('Justify',
                                      'Tooltip',
                                      'Format')):
            self.treeview.append_column(self._create_text_column(title,
                                                                 (i + 4)))

        self.treeview.append_column(self._create_int_column('Width', 7))
        self.treeview.append_column(self._create_bool_column('Sorted', 8))
        self.treeview.append_column(self._create_text_column('Order', 9))
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.treeview)
        self.vbox.pack_start(sw, True, True)
        label = gtk.Label()
        instructions = """<small>Valid values:
        <b>Data type:</b> str, int, float or date
        <b>Justify:</b> left, center or right
        <b>Order:</b> ascending or descending</small>"""
        label.set_alignment(0.0, 0.0)
        label.set_markup(instructions)
        self.vbox.pack_start(label, False, False)

    def _create_text_column(self, title, index):
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', self._on_text_renderer__edited, index)
        col = gtk.TreeViewColumn(title, renderer, text=index)
        return col

    def _create_bool_column(self, title, index):
        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_toggle_renderer__toggled, index)
        col = gtk.TreeViewColumn(title, renderer, active=index)
        return col

    def _create_int_column(self, title, index):
        col = self._create_text_column(title, index)
        return col

    def _get_default_values(self):
        return ('', '', 'str', True, 'left', '', '', 0, False, '')

    def _update_proxy(self):
        cols = []
        for column in self.model:
            cols.append('|'.join(map(str, tuple(column))))

        data = '^'.join(cols)
        self.proxy.set_value(data)

    def _load_columns(self):
        self.model.clear()
        cd = self.gwidget.get_glade_property('column-definitions').value
        if not cd:
            return
        
        for col in cd.split('^'):
            (attr, title, data_type,
             visible, justify, tooltip,
             format, width, sorted, order) = col.split('|')
            
            visible = get_bool_from_string_with_default(visible, True)
            width = int(width)
            sorted = get_bool_from_string_with_default(sorted, False)
            self.model.append((attr, title, data_type,
                               visible, justify, tooltip,
                               format, width, sorted, order))

    def _on_add_clicked(self, button):
        row_iter = self.model.append(self._get_default_values())
        path = self.model.get_path(row_iter)
        col = self.treeview.get_column(0)
        self.treeview.set_cursor(path, col, True)
        self._update_proxy()

    def _on_remove_clicked(self, button):
        model, selected_iter = self.treeview.get_selection().get_selected()
        if selected_iter:
            model.remove(selected_iter)
            self._update_proxy()

    def _on_up_clicked(self, button):
        model, selected_iter = self.treeview.get_selection().get_selected()
        if not selected_iter:
            return
        
        path = self.model.get_path(selected_iter)
        prev_iter = self.model.get_iter(((path[0] - 1)))
        if not prev_iter:
            return
        
        model.swap(prev_iter, selected_iter)
        self._update_proxy()
        self._update_buttons()

    def _on_down_clicked(self, button):
        model, selected_iter = self.treeview.get_selection().get_selected()
        if not selected_iter:
            return
        
        next_iter = model.iter_next(selected_iter)
        if not next_iter:
            return
        
        model.swap(selected_iter, next_iter)
        self._update_proxy()
        self._update_buttons()

    def _on_text_renderer__edited(self, renderer, path, new_text, col_index):
        value = new_text
        if col_index == WIDTH:
            try:
                value = int(new_text)
            except ValueError:
                return

        row = self.model[path[0]]
        row[col_index] = value
        if col_index == ATTRIBUTE:
            title = row[TITLE]
            if not title:
                row[TITLE] = value.capitalize()
        self._update_proxy()

    def _on_toggle_renderer__toggled(self, renderer, path, col_index):
        row = self.model[path[0]]
        row[col_index] = not row[col_index]
        self._update_proxy()

    def _on_selection__changed(self, selection):
        self._update_buttons()

    def _update_buttons(self):
        selection = self.treeview.get_selection()
        model, selected_iter = selection.get_selected()
        if not selected_iter:
            self.remove.set_sensitive(False)
            self.down.set_sensitive(False)
            self.up.set_sensitive(False)
            return
        
        self.remove.set_sensitive(True)
        path = model.get_path(selected_iter)[0]
        size = len(model)
        if path == 0:
            self.up.set_sensitive(False)
            if size > 1:
                self.down.set_sensitive(True)
                
        if path == size - 1:
            self.down.set_sensitive(False)
            if size > 1:
                self.up.set_sensitive(True)
                
        if path > 0 and path < (size - 1):
            self.up.set_sensitive(True)
            self.down.set_sensitive(True)
