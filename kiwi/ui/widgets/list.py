#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2005 Async Open Source
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
#            Gustavo Rahal <gustavo@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""Defines an enhanced version of GtkTreeView"""

import datetime

import gobject
import gtk

from kiwi import _warn, datatypes, ValueUnset
from kiwi.accessors import kgetattr
from kiwi.utils import PropertyObject, slicerange, gsignal, gproperty

# Minimum number of rows where we show busy cursor when sorting numeric columns
MANY_ROWS = 1000

str2type = datatypes.converter.str_to_type

def str2enum(value_name, enum_class):
    "converts a string to a enum"
    for _, enum in enum_class.__enum_values__.items():
        if value_name in (enum.value_name, enum.value_nick):
            return enum

def str2bool(value, default_value=False,
             from_string=datatypes.converter.from_string):
    "converts a boolean to a enum"
    return from_string(bool, value, default_value)

class Column(PropertyObject, gobject.GObject):
    """Specifies a column in a List"""
    gproperty('title', str)
    gproperty('data-type', object)
    gproperty('visible', bool, default=True)
    gproperty('justify', gtk.Justification, default=gtk.JUSTIFY_LEFT)
    gproperty('format', str)
    gproperty('width', int, maximum=2**16)
    gproperty('sorted', bool, default=False)
    gproperty('order', gtk.SortType, default=gtk.SORT_ASCENDING)
    #gproperty('title_pixmap', str)
    gproperty('expand', bool, default=False)
    gproperty('tooltip', str)
    gproperty('format_func', object)
    gproperty('editable', bool, default=False)
    
    def __init__(self, attribute, title=None, data_type=None, **kwargs):
        """
        Creates a new Column, which describes how a column in a
        List should be rendered.

          - attribute: a string with the name of the instance attribute the
            column represents.
          - title: the title of the column, defaulting to the capitalized form
            of the attribute.
          - data_type: the type of the attribute that will be inserted into the
            column.
            
          Optional keyword arguments:
          - visible: a boolean specifying if it is initially hidden or shown.
          - justify: one of gtk.JUSTIFY_LEFT, gtk.JUSTIFY_RIGHT or
            gtk.JUSTIFY_CENTER or None. If None, the justification will be
            determined by the type of the attribute value of the first
            instance to be inserted in the List (integers and floats
            will be right-aligned).
          - format: a format string to be applied to the attribute value upon
            insertion in the list.
          - width: the width in pixels of the column, if not set, uses the
            default to List. If no Column specifies a width,
            columns_autosize() will be called on the List upon add_instance()
            or the first add_list().
          - sorted: whether or not the List is to be sorted by this column.
            If no Columns are sorted, the List will be created unsorted.
          - order: one of gtk.SORT_ASCENDING or gtk.SORT_DESCENDING or -1. The
            value -1 is used internally when the column is not sorted.
          - expand: if set column will expand. Note: this space is shared
            equally amongst all columns that have the expand set to True.
          - tooltip: a string which will be used as a tooltip for the column
            header
          - format_func: a callable which will be used to format the output
            of a column. The function will take one argument which is the
            value to convert and is expected to return a string.
            Note that you cannot use format and format_func at the same time,
            if you provide a format function you'll be responsible for
            converting the value to a string.
          - editable: if true the field is editable and when you modify the
            contents of the cell the model will be updated.
          TODO
          - title_pixmap: if set to a filename a pixmap will be used *instead*
            of the title set. The title string will still be used to
            identify the column in the column selection and in a tooltip,
            if a tooltip is not set.
        """
        
        # XXX: filter function?
        if ' ' in attribute:
            msg = ("The attribute can not contain spaces, otherwise I can"
                   " not find the value in the instances: %s" % attribute)
            raise AttributeError(msg)
        
        self.attribute = attribute

        kwargs['title'] = title or attribute.capitalize()
        if data_type:
            kwargs['data_type'] = data_type

        format_func = kwargs.get('format_func')
        if format_func:
            if not callable(format_func):
                raise TypeError("format_func must be callable")
            if 'format' in kwargs:
                raise TypeError(
                    "format and format_func can not be used at the same time")
        
        PropertyObject.__init__(self, **kwargs)
        gobject.GObject.__init__(self)

    # This is meant to be subclassable, we're using kgetattr, as
    # a staticmethod as an optimization, so we can avoid a function call.
    get_attribute = staticmethod(kgetattr)
                                             
    def __repr__(self):
        ns = self.__dict__.copy()
        attr = ns['attribute']
        del ns['attribute']
        return "<%s %s: %s>" % (self.__class__.__name__, attr, ns)

    # XXX: Replace these two with a gazpacho loader adapter
    def __str__(self):
        if self.data_type is None:
            data_type = ''
        else:
            data_type = self.data_type.__name__

        return "%s|%s|%s|%s|%d|%s|%s|%d|%s|%d" % \
               (self.attribute, self.title, data_type, self.visible,
                self.justify, self.tooltip, self.format, self.width,
                self.sorted, self.order)
    
    def from_string(cls, data_string):
        fields = data_string.split('|')
        if len(fields) != 10:
            msg = 'every column should have 10 fields, not %d' % len(fields)
            raise ValueError(msg)

        # the attribute is mandatory
        if not fields[0]:
            raise TypeError
        
        column = cls(fields[0])
        column.title = fields[1] or ''
        column.data_type = str2type(fields[2])
        column.visible = str2bool(fields[3], default_value=True)
        column.justify = str2enum(fields[4], gtk.JUSTIFY_LEFT)
        column.tooltip = fields[5]
        column.format = fields[6]

        try:
            column.width = int(fields[7])
        except ValueError:
            pass
        
        column.sorted = str2bool(fields[8], default_value=False)
        column.order = str2enum(fields[9], gtk.SORT_ASCENDING) \
                     or gtk.SORT_ASCENDING
        # XXX: expand, remember to sync with __str__
        
        return column
    from_string = classmethod(from_string)
    
class ContextMenu(gtk.Menu):
    """
    ContextMenu is a wrapper for the menu that's displayed when right
    clicking on a column header. It monitors the treeview and rebuilds
    when columns are added, removed or moved.
    """
    
    def __init__(self, treeview):
        gtk.Menu.__init__(self)
        
        self._dirty = True
        self._signal_ids = []
        self._treeview = treeview
        self._treeview.connect('columns-changed',
                              self._on_treeview__columns_changed)
        self._create()
        
    def clean(self):
        for child in self.get_children():
            self.remove(child)
            
        for menuitem, signal_id in self._signal_ids:
            menuitem.disconnect(signal_id)
        self._signal_ids = []

    def popup(self, event):
        self._create()
        gtk.Menu.popup(self, None, None, None,
                       event.button, event.time)
        
    def _create(self):
        if not self._dirty:
            return
        
        self.clean()
        
        for column in self._treeview.get_columns():
            header_widget = column.get_widget()
            title = header_widget.get_text()
                
            menuitem = gtk.CheckMenuItem(title)
            menuitem.set_active(column.get_visible())
            signal_id = menuitem.connect("activate",
                                         self._on_menuitem__activate,
                                         column)
            self._signal_ids.append((menuitem, signal_id))
            menuitem.show()
            self.append(menuitem)
            
        self._dirty = False

    def _on_treeview__columns_changed(self, treeview):
        self._dirty = True
        
    def _on_menuitem__activate(self, menuitem, column):
        active = menuitem.get_active()
        column.set_visible(active)

        children = self.get_children()

        if active:
            # Make sure all items are selectable
            for child in children:
                child.set_sensitive(True)
        else:
            # Protect so we can't hide all the menu items
            # If there's only one menuitem less to select, set
            # it to insensitive
            active_children = [child for child in children
                                         if child.get_active()]
            if len(active_children) == 1:
                active_children[0].set_sensitive(False)

COL_MODEL = 0

class List(gtk.ScrolledWindow):
    """An enhanced version of GtkTreeView, which provides pythonic wrappers
    for accessing rows, and optional facilities for column sorting (with
    types) and column selection."""
    
    gsignal('selection-changed', object)
    gsignal('double-click', object)

    # this property is used to serialize the columns of a List. The format
    # is a big string with '^' as the column separator and '|' as the field
    # separator
    gproperty('column-definitions', str, nick="ColumnDefinitions")
    gproperty('selection-mode', gtk.SelectionMode,
              default=gtk.SELECTION_BROWSE, nick="SelectionMode")
    
    def __init__(self, columns=[],
                 instance_list=None,
                 mode=gtk.SELECTION_BROWSE):
        
        # allow to specify only one column
        if isinstance(columns, Column):
            columns = [columns]
        elif not isinstance(columns, list):
            raise TypeError("columns must be a list or a Column")

        if not isinstance(mode, gtk.SelectionMode):
            raise TypeError("mode must be an gtk.SelectionMode enum")
        elif mode == gtk.SELECTION_EXTENDED:
            raise TypeError("gtk.SELECTION_EXTENDED is deprecated")
        
        gtk.ScrolledWindow.__init__(self)
        # we always want a vertical scrollbar. Otherwise the button on top
        # of it doesn't make sense. This button is used to display the popup
        # menu
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

        self._columns_configured = False
        self._autosize = True
        
        self._model = gtk.ListStore(object)
        self._model.set_sort_func(COL_MODEL, self._sort_function)
        self._treeview = gtk.TreeView(self._model)
        self._treeview.show()
        self.add(self._treeview)

        self._treeview.set_rules_hint(True)

        # these tooltips are used for the columns
        self._tooltips = gtk.Tooltips()

        # convenience connections
        self._treeview.connect_after("row-activated",
                                    self._after_treeview__row_activated)

        # create a popup menu for showing or hiding columns
        self._popup = ContextMenu(self._treeview)

        # when setting the column definition the columns are created
        self.set_columns(columns)

        # by default we are unordered. This index points to the column
        # definition of the column that dictates the order, in case there is
        # any
        self._sort_column_index = -1

        if instance_list:
            self._treeview.freeze_notify()
            self._load(instance_list)
            self._treeview.thaw_notify()

        if self._sort_column_index != -1:
            column = self._columns[self._sort_column_index]
            self._model.set_sort_column_id(COL_MODEL, column.order)

        # Set selection mode last to avoid spurious events
        selection = self._treeview.get_selection()
        selection.connect("changed", self._on_selection__changed)
        selection.set_mode(mode)

        # Select the first item if no items are selected
        if mode != gtk.SELECTION_NONE and instance_list:
            selection.select_iter(self._model[COL_MODEL].iter)

    # Python list object implementation
    # These methods makes the kiwi list behave more or less
    # like a normal python list
    #
    # TODO:
    #   methods
    #      append, count, extend, index, insert,
    #      pop, remove, reverse, sort
    #
    #   operators
    #      __add__, __eq__, __ge__, __gt__, __iadd__,
    #      __imul__,  __le__, __lt__, __mul__, __ne__,
    #      __rmul__
    #
    #   misc
    #     __delitem__, __hash__, __reduce__, __reduce_ex__
    #     __reversed__

    def __len__(self):
        "len(list)"
        return len(self._model)

    def __nonzero__(self):
        "if list"
        return True

    def __contains__(self, instance):
        "item in list"
        for row in self._model:
            if row[COL_MODEL] == instance:
                return True
        return False

    def __iter__(self):
        "for item in list"
        class ModelIterator:
            def __init__(self):
                self._index = -1
                
            def next(self, model=self._model):
                try:
                    self._index += 1
                    return model[self._index][COL_MODEL]
                except IndexError:
                    raise StopIteration
                
        return ModelIterator()
    
    def __getitem__(self, arg):
        "list[n]"
        if isinstance(arg, (int, gtk.TreeIter, str)):
            item = self._model[arg][COL_MODEL]
        elif isinstance(arg, slice):
            model = self._model
            return [model[item][COL_MODEL]
                        for item in slicerange(arg, len(self._model))]
        else:
            raise TypeError("argument arg must be int, gtk.Treeiter or "
                            "slice, not %s" % type(arg))
        return item

    def __setitem__(self, arg, item):
        "list[n] = m"
        if isinstance(arg, (int, gtk.TreeIter, str)):
            self._model[arg] = (item,)
        elif isinstance(arg, slice):
            raise NotImplementedError("slices for list are not implemented")
        else:
            raise TypeError("argument arg must be int or gtk.Treeiter,"
                            " not %s" % type(arg))
    
    # GObject property handling
    def do_get_property(self, pspec):
        if pspec.name == 'column-definitions':
            return self.get_columns()
        elif pspec.name == 'selection-mode':
            return self.get_selection_mode()
        else:
            raise AttributeError('Unknown property %s' % pspec.name)

    def do_set_property(self, pspec, value):
        if pspec.name == 'column-definitions':
            self.set_columns(value)
        elif pspec.name == 'selection-mode':
            self.set_selection_mode(value)
        else:
            raise AttributeError('Unknown property %s' % pspec.name)

    # Columns handling
    def _load(self, instance_list, progress_handler=None):
        # do nothing if empty list or None provided
        if not instance_list: 
            return

        instance = instance_list[0]
        if not self._has_enough_type_information():
            self._guess_types(instance)
            self._setup_columns()
            
        model = self._model
        # In the case of an empty model, select the first instance
        if not len(model):
            # Append the first instance, so we can get a reference to
            # the iterator so we later can select it
            instance_iter = self._model.append((instance,))
            
            # Slice out the first, already inserted instance, the
            # rest of the list is inserted below
            instance_list = instance_list[1:]

            # Finally select the iterator, but only if we allow
            # items to be selectable
            selection = self._treeview.get_selection()
            if selection.get_mode() != gtk.SELECTION_NONE:
                selection.select_iter(instance_iter)
            
        for instance in instance_list:
            model.append((instance,))
            
        # As soon as we have data for that list, we can autosize it, and
        # we don't want to autosize again, or we may cancel user
        # modifications.
        if self._autosize:
            self._treeview.columns_autosize()
            self._autosize = False
        
    def _guess_types(self, instance):
        """Iterates through columns, using the type attribute when found or
        the type of the associated attribute from the sample instance provided.
        """
        for column in self._columns:
            if column.data_type is None:
                column.data_type = self._guess_type(column, instance)

    def _guess_type(self, column, instance):
        
        # steal attribute from sample instance and use its type
        value = column.get_attribute(instance, column.attribute, ValueUnset)
        if value is ValueUnset:
            raise TypeError("Failed to get attribute '%s' for %s" %
                            (column.attribute, instance))
            
        tp = type(value)
        if tp is type(None):
            raise TypeError("Detected invalid type None for column `%s'; "
                            "please specify type in Column constructor.""" %
                            column.attribute)
        return tp
    
    def _setup_columns(self):
        if self._columns_configured:
            return
        
        for column in self._columns:
            self._setup_column(column)

        self._columns_configured = True

    def _setup_column(self, column):
        # You can't subclass bool, so this is okay
        if (column.data_type is bool and column.format):
            raise TypeError("format is not supported for boolean columns") 

        index = self._columns.index(column)
        treeview_column = self._treeview.get_column(index)
        if treeview_column is None:
            treeview_column = self._create_column(column)  
            
        renderer, renderer_prop = self._guess_renderer_for_type(column)
        
        justify = column.justify
        # If we don't specify a justification, right align it for int/float
        # and left align it for everything else. 
        if (justify is None and 
            issubclass(column.data_type, (int, float))):
            justify = gtk.JUSTIFY_RIGHT
        else:
            justify = gtk.JUSTIFY_LEFT
            
        if justify is not None:
            if justify == gtk.JUSTIFY_RIGHT:
                xalign = 1.0
            elif justify == gtk.JUSTIFY_CENTER:
                xalign = 0.5
            elif justify == gtk.JUSTIFY_LEFT:
                xalign = 0.0
            else:
                raise AssertionError
            renderer.set_property("xalign", xalign)
            
        treeview_column.pack_start(renderer)
        treeview_column.set_cell_data_func(renderer, self._cell_data_func,
                                           (column, renderer_prop))
        treeview_column.set_visible(column.visible)

        treeview_column.connect("clicked", self._on_column__clicked, column)
        if column.width:
            treeview_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            treeview_column.set_fixed_width(column.width)
        if column.tooltip:
            widget = self._get_column_button(treeview_column)
            if widget is not None:
                self._tooltips.set_tip(widget, column.tooltip)

        if column.expand:
            # Default is False
            treeview_column.set_expand(True)

        if column.sorted:
            self._sort_column_index = index
            treeview_column.set_sort_indicator(True)
            
        if column.width:
            self._autosize = False

        # typelist here may be none. It's okay; justify_columns will try
        # and use the specified justifications and if not present will
        # not touch the column. When typelist is not set,
        # add_instance/add_list have a chance to fix up the remaining
        # justification by looking at the first instance's data.
#        self._justify_columns(columns, typelist)

    def _has_enough_type_information(self):
        """True if all the columns has a type set.
        This is used to know if we can create the treeview columns.
        """
        for column in self._columns:
            if column.data_type is None:
                return False
        return True
        
    def _create_column(self, column):
        treeview_column = gtk.TreeViewColumn()
        # we need to set our own widget because otherwise
        # __get_column_button won't work

        label = gtk.Label(column.title)
        label.show()
        treeview_column.set_widget(label)
        treeview_column.set_resizable(True)
        treeview_column.set_clickable(True)
        treeview_column.set_reorderable(True)
        self._treeview.append_column(treeview_column)

        # setup the button to show the popup menu
        button = self._get_column_button(treeview_column)
        button.connect('button-release-event',
                       self._on_header__button_release_event)
        return treeview_column
    
    def _on_renderer_text__edited(self, renderer, path, text,
                                  model, attribute, column):
        obj = model[path][COL_MODEL]
        value = datatypes.converter.from_string(column.data_type, text)
        setattr(obj, attribute, value)
        
    def _guess_renderer_for_type(self, column):
        """Gusses which CellRenderer we should use for a given type.
        It also set the property of the renderer that depends on the model,
        in the renderer.
        """
        
        # TODO: Move to column
        data_type = column.data_type
        if issubclass(data_type, (datetime.date,  basestring, int, float)):
            renderer = gtk.CellRendererText()
            prop = 'text'
            if column.editable:
                renderer.set_property('editable', True)
                renderer.connect('edited', self._on_renderer_text__edited,
                                 self._model, column.attribute, column)

        elif data_type is bool:
            renderer = gtk.CellRendererToggle()
            # TODO: radio, activatable
            prop = 'active'
        else:
            raise ValueError("the type %s is not supported yet" % data_type)

        return renderer, prop
    
    def _cell_data_func(self, tree_column, renderer, model, iter,
                        (column, renderer_prop)):
        data = column.get_attribute(model[iter][COL_MODEL],
                                    column.attribute, None)
        if column.format:
            data = datatypes.lformat(column.format, data)
        elif column.format_func:
            data = column.format_func(data)
        renderer.set_property(renderer_prop, data)

    def _on_header__button_release_event(self, button, event):
        if event.button == 3:
            self._popup.popup(event)
            return False

        return False

    def _on_renderer__edited(self, renderer, path, value, column):
        data_type = column.data_type
        if data_type in (int, float):
            value = data_type(value)
            
        # XXX convert new_text to the proper data type
        setattr(self._model[path][COL_MODEL], column.attribute, value)
        
    def _on_renderer__toggled(self, renderer, path, column):
        setattr(self._model[path][COL_MODEL], column.attribute,
                not renderer.get_active())

    def _clear_columns(self):
        while self._treeview.get_columns():
            self._treeview.remove_column(self._treeview.get_column(COL_MODEL))

        self._popup.clean()

        self._columns_configured = False
        
    # selection methods
    def _find_iter_from_data(self, instance):
        for row in self._model:
            if instance == row[COL_MODEL]:
                return row.iter

    def _select_and_focus_row(self, row_iter):
        self._treeview.set_cursor(self._model[row_iter].path)
                    
    def _sort_function(self, model, iter1, iter2):
        column = self._columns[self._sort_column_index]
        attr = column.attribute
        return cmp(column.get_attribute(model[iter1][COL_MODEL], attr),
                   column.get_attribute(model[iter2][COL_MODEL], attr))

    def _on_column__clicked(self, treeview_column, column):
        if self._sort_column_index == -1:
            # this mean we are not sorting at all
            return

        old_treeview_column = self._treeview.get_column(
            self._sort_column_index)
        old_treeview_column.set_sort_indicator(False)
        
        # reverse the old order or start with SORT_DESCENDING if there was no
        # previous order
        column_index = self._columns.index(column)
        self._sort_column_index = column_index

        # maybe it's the first time this column is ordered
        if column.order is None:
            column.order = gtk.SORT_DESCENDING

        # reverse the order
        old_order = column.order
        if old_order == gtk.SORT_ASCENDING:
            new_order = gtk.SORT_DESCENDING
        else:
            new_order = gtk.SORT_ASCENDING
        column.order = new_order

        # cosmetic changes
        treeview_column.set_sort_indicator(True)
        treeview_column.set_sort_order(new_order)

        # This performs the actual ordering
        self._model.set_sort_column_id(COL_MODEL, new_order)

    # handlers
    def _on_selection__changed(self, selection):
        mode = selection.get_mode()
        if mode == gtk.SELECTION_MULTIPLE:
            item = self.get_selected_rows()
        elif mode in (gtk.SELECTION_SINGLE, gtk.SELECTION_BROWSE):
            item = self.get_selected()
        else:
            raise AssertionError
        self.emit('selection-changed', item)
        
    def _after_treeview__row_activated(self, treeview, path, view_column):
        self.emit('double-click', self._model[path][COL_MODEL])
        
    def _get_iter_from_instance(self, instance):
        """Returns the treeiter where this instance is using a linear search.
        If the instance is not in the list it returns None
        """
        for row in self._model:
            if row[COL_MODEL] is instance:
                return row.iter

    def get_iter(self, instance):
        treeiter = self._get_iter_from_instance(instance)
        if not treeiter:
            raise ValueError("The instance %s is not in the list." % instance)
        return treeiter
        
    # hacks
    def _get_column_button(self, column):
        """Return the button widget of a particular TreeViewColumn.

        This hack is needed since that widget is private of the TreeView but
        we need access to them for Tooltips, right click menus, ...

        Use this function at your own risk
        """
        
        button = column.get_widget()
        assert button is not None, ("You must call column.set_widget() "
                                    "before calling _get_column_button")
        
        while not isinstance(button, gtk.Button):
            button = button.get_parent()

        return button

    # start of the hack to put a button on top of the vertical scrollbar
    def _setup_popup_button(self):
        """Put a button on top of the vertical scrollbar to show the popup
        menu.
        Internally it uses a POPUP window so you can tell how *Evil* is this.
        """
        self._popup_window = gtk.Window(gtk.WINDOW_POPUP)
        self._popup_button = gtk.Button('*')
        self._popup_window.add(self._popup_button)
        self._popup_window.show_all()
        
        self.forall(self._find_vertical_scrollbar)
        self.connect('size-allocate', self._on_scrolled_window__size_allocate)
        self.connect('realize', self._on_scrolled_window__realize)

    def _find_vertical_scrollbar(self, widget):
        """This method is called from a .forall() method in the ScrolledWindow.
        It just save a reference to the vertical scrollbar for doing evil
        things later.
        """
        if isinstance(widget, gtk.VScrollbar):
            self._vscrollbar = widget

    def _get_header_height(self):
        treeview_column = self._treeview.get_column(0)
        button = self._get_column_button(treeview_column)
        alloc = button.get_allocation()
        return alloc.height

    def _on_scrolled_window__realize(self, widget):
        toplevel = widget.get_toplevel()
        self._popup_window.set_transient_for(toplevel)
        self._popup_window.set_destroy_with_parent(True)
        
    def _on_scrolled_window__size_allocate(self, widget, allocation):
        """Resize the Vertical Scrollbar to make it smaller and let space
        for the popup button. Also put that button there.
        """
        old_alloc = self._vscrollbar.get_allocation()
        height = self._get_header_height()
        new_alloc = gtk.gdk.Rectangle(old_alloc.x, old_alloc.y + height,
                                      old_alloc.width,
                                      old_alloc.height - height)
        self._vscrollbar.size_allocate(new_alloc)
        # put the popup_window in its position
        gdk_window = self.window
        if gdk_window:
            x, y = gdk_window.get_origin()
            self._popup_window.move(x + old_alloc.x, y + old_alloc.y)
        
    # end of the popup button hack

    #
    # Public API
    #
    def get_model(self):
        "Return treemodel of the current list"
        return self._model

    def get_treeview(self):
        "Return treeview of the current list"
        return self._treeview
    
    def get_columns(self):
        return self._columns_string

    def get_column_by_name(self, name):
        """Returns the name of a column"""
        for column in self._columns:
            if column.attribute == name:
                return column

        raise LookupError("There is no column called %s" % name)
    
    def set_columns(self, value):
        """This function can be called in two different ways:
         - value is a string with the column definitions in a special format
           (see column-definitions property at the beginning of this class)

         - value is a list/tuple of Column objects
        """
        
        if isinstance(value, basestring):
            self._columns_string = value
            self._columns = []            
            for col in value.split('^'):
                if not col:
                    continue
                c = Column.from_string(col)
                self._columns.append(c)
        elif isinstance(value, (list, tuple)):
            self._columns = value
            self._columns_string = '^'.join([str(col) for col in value])
        else:
            raise ValueError("value should be a string of a list of columns")

        self._clear_columns()
        if self._has_enough_type_information():
            self._setup_columns()
        
    def add_instance(self, instance, select=False):
        """Adds an instance to the list.
        - instance: the instance to be added (according to the columns spec)
        - select: whether or not the new item should appear selected.
        """

        if not self._has_enough_type_information():
            self._guess_types(instance)
            self._setup_columns()

        # Freeze and save original selection mode to avoid blinking
        self._treeview.freeze_notify()

        row_iter = self._model.append((instance,))
        if self._autosize:
            self._treeview.columns_autosize()

        if select:
            self._select_and_focus_row(row_iter)
        self._treeview.thaw_notify()

    def remove_instance(self, instance):
        """Remove an instance from the list.
        If the instance is not in the list it returns False. Otherwise it
        returns True.
        """
        if not self._has_enough_type_information():
            raise RuntimeError(("There is no columns neither data on the "
                                "list yet so you can not remove any instance"))

        # linear search for the instance to remove
        treeiter = self._get_iter_from_instance(instance)
        if treeiter:
            self._model.remove(treeiter)
            return True
            
        return False

    def update_instance(self, new_instance):
        treeiter = self.get_iter(new_instance)
        self._model.row_changed(self._model[treeiter].path, treeiter)
        
    def set_column_visibility(self, column_index, visibility):
        treeview_column = self._treeview.get_column(column_index)
        treeview_column.set_visible(visibility)

    def get_selection_mode(self):
        selection = self._treeview.get_selection()
        if selection:
            return selection.get_mode()
    
    def set_selection_mode(self, mode):
        selection = self._treeview.get_selection()
        if selection:
            self.notify('selection-mode')
            return selection.set_mode(mode)

    def unselect_all(self):
        selection = self._treeview.get_selection()
        if selection:
            selection.unselect_all()

    def select_instance(self, instance):
        selection = self._treeview.get_selection()
        if selection:
            treeiter = self.get_iter(instance)
            if treeiter:
                selection.select_iter(treeiter)

    def get_selected(self):
        """Returns the currently selected object
        If an object is not selected, None is returned
        """
        selection = self._treeview.get_selection()
        if not selection:
            # AssertionError ?
            return

        mode = selection.get_mode()
        if mode == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed in %r mode" % mode)
        elif mode not in (gtk.SELECTION_SINGLE, gtk.SELECTION_BROWSE):
            _warn('get_selected() called when multiple rows can be selected')

        model, iter = selection.get_selected()
        if iter:
            return model[iter][COL_MODEL]

    def get_selected_rows(self):
        """Returns a list of currently selected objects
        If no objects are selected an empty list is returned
        """
        selection = self._treeview.get_selection()
        if not selection:
            # AssertionError ?
            return
        
        mode = selection.get_mode()
        if mode == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed in %r mode" % mode)
        elif mode in (gtk.SELECTION_SINGLE, gtk.SELECTION_BROWSE):
            _warn('get_selected_rows() called when only a single row '
                  'can be selected')

        model, paths = selection.get_selected_rows()
        if paths:
            return [model[path][COL_MODEL] for (path,) in paths]
        return []
    
    def add_list(self, list, clear=True, progress_handler=None):
        """
        Allows a list to be loaded, by default clearing it first.
        freeze() and thaw() are called internally to avoid flashing.
        
          - list: a list to be added
          - clear: a boolean that specifies whether or not to clear the list
          - progress_handler: a callback function to be called while the list
            is being filled
        """

        self._treeview.freeze_notify()

        if clear:
            self.unselect_all()
            self._model.clear()

        ret = self._load(list, progress_handler)
            
        self._treeview.thaw_notify()
        return ret

    def clear(self):
        """Removes all the instances of the list"""
        self._treeview.freeze_notify()
        self._model.clear()
        self._treeview.thaw_notify()
        
gobject.type_register(List)

if __name__ == '__main__':
    win = gtk.Window()
    win.set_default_size(300, 150)
    win.connect('destroy', gtk.main_quit)

    class Person:
        """The parameters need to be of the same name of the column headers"""
        def __init__(self, name, age, city, single):
            (self.name,
             self.age,
             self.city,
             self.single) = name, age, city, single

    columns = (
        Column('name', sorted=True, tooltip='What about a stupid tooltip?'),
        Column('age'),
        Column('city', visible=True),
        Column('single', title='Single?')
        )
    
    data = (Person('Evandro', 23, 'Belo Horizonte', False),
            Person('Daniel', 22, 'Sao Carlos', False),
            Person('Henrique', 21, 'Sao Carlos', True),
            Person('Gustavo', 23, 'San Jose do Santos', True),
            Person('Johan', 23, 'Goteborg', True), 
            Person('Lorenzo', 26, 'Granada', True)
        )

    l = List(columns, data)

    # add an extra person
    l.add_instance(Person('Nando', 29, 'Santos', False))

    win.add(l)
    win.show_all()
    
    gtk.main()
