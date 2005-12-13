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

"""High level wrapper for GtkTreeView"""

import datetime
import gettext

import gobject
import gtk
from gtk import gdk

from kiwi import _warn, ValueUnset
from kiwi.accessors import kgetattr
from kiwi.datatypes import converter, currency, lformat
from kiwi.decorators import deprecated
from kiwi.python import slicerange
from kiwi.utils import PropertyObject, gsignal, gproperty, type_register

_ = gettext.gettext

str2type = converter.str_to_type

def str2enum(value_name, enum_class):
    "converts a string to a enum"
    for _, enum in enum_class.__enum_values__.items():
        if value_name in (enum.value_name, enum.value_nick):
            return enum

def str2bool(value, from_string=converter.from_string):
    "converts a boolean to a enum"
    return from_string(bool, value)

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
    gproperty('searchable', bool, default=False)
    gproperty('radio', bool, default=False)
    gproperty('cache', bool, default=False)
    
    # This can be set in subclasses, to be able to allow custom
    # cell_data_functions, used by SequentialColumn
    cell_data_func = None

    # This is called after the renderer property is set, to allow
    # us to set custom rendering properties
    renderer_func = None

    # This is called when the renderer is created, so we can set/fetch
    # initial properties
    on_attach_renderer = None
    
    def __init__(self, attribute, title=None, data_type=None, **kwargs):
        """
        Creates a new Column, which describes how a column in a
        List should be rendered.

        @param attribute: a string with the name of the instance attribute the
            column represents.
        @param title: the title of the column, defaulting to the capitalized
            form of the attribute.
        @param data_type: the type of the attribute that will be inserted
            into the column.

        @keyword visible: a boolean specifying if it is initially hidden or
            shown.
        @keyword justify: one of gtk.JUSTIFY_LEFT, gtk.JUSTIFY_RIGHT or
            gtk.JUSTIFY_CENTER or None. If None, the justification will be
            determined by the type of the attribute value of the first
            instance to be inserted in the List (integers and floats
            will be right-aligned).
        @keyword format: a format string to be applied to the attribute
            value upon insertion in the list.
        @keyword width: the width in pixels of the column, if not set, uses the
            default to List. If no Column specifies a width,
            columns_autosize() will be called on the List upon append()
            or the first add_list().
        @keyword sorted: whether or not the List is to be sorted by this column.
            If no Columns are sorted, the List will be created unsorted.
        @keyword order: one of gtk.SORT_ASCENDING or gtk.SORT_DESCENDING or
            -1. The value -1 is used internally when the column is not sorted.
        @keyword expand: if set column will expand. Note: this space is shared
            equally amongst all columns that have the expand set to True.
        @keyword tooltip: a string which will be used as a tooltip for
            the column header
        @keyword format_func: a callable which will be used to format
            the output of a column. The function will take one argument
            which is the value to convert and is expected to return a string.
            Note that you cannot use format and format_func at the same time,
            if you provide a format function you'll be responsible for
            converting the value to a string.
        @keyword editable: if true the field is editable and when you modify the
            contents of the cell the model will be updated.
        @keyword searchable: if true the attribute values of the column can
            be searched using type ahead search. Only string attributes are
            currently supported.
        @keyword radio: If true render the column as a radio instead of toggle.
            Only applicable for columns with boolean data types.
        @keyword cache: If true, the value will only be fetched once,
            and the same value will be reused for futher access.
        @keyword title_pixmap: (TODO) if set to a filename a pixmap will be
            used *instead* of the title set. The title string will still be
            used to identify the column in the column selection and in a
            tooltip, if a tooltip is not set.
        """
        
        # XXX: filter function?
        if ' ' in attribute:
            msg = ("The attribute can not contain spaces, otherwise I can"
                   " not find the value in the instances: %s" % attribute)
            raise AttributeError(msg)
 
        self.attribute = attribute
        self.compare = None
        self.as_string = None
        self.from_string = None

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

    def prop_set_data_type(self, data):
        if data is not None:
            conv = converter.get_converter(data)
            self.compare = conv.get_compare_function()
            self.as_string = conv.as_string
            self.from_string = conv.from_string
        return data
    
    def __repr__(self):
        namespace = self.__dict__.copy()
        attr = namespace['attribute']
        del namespace['attribute']
        return "<%s %s: %s>" % (self.__class__.__name__, attr, namespace)

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
        column.visible = str2bool(fields[3])
        column.justify = str2enum(fields[4], gtk.JUSTIFY_LEFT)
        column.tooltip = fields[5]
        column.format = fields[6]

        try:
            column.width = int(fields[7])
        except ValueError:
            pass
        
        column.sorted = str2bool(fields[8])
        column.order = str2enum(fields[9], gtk.SORT_ASCENDING) \
                     or gtk.SORT_ASCENDING
        
        # XXX: expand, remember to sync with __str__
        
        return column
    from_string = classmethod(from_string)

class SequentialColumn(Column):
    """I am a column which will display a sequence of numbers, which
    represent the row number. The value is independent of the data in
    the other columns, so no matter what I will always display 1 in
    the first column, unless you reverse it by clicking on the column
    header.

    If you don't give me any argument I'll have the title of a hash (#) and
    right justify the sequences."""
    def __init__(self, title='#', justify=gtk.JUSTIFY_RIGHT, **kwargs):
        Column.__init__(self, '_kiwi_sequence_id',
                        title=title, justify=justify, data_type=int, **kwargs)

    def cell_data_func(self, tree_column, renderer, model, treeiter,
                       (column, renderer_prop, as_string)):
        reversed = tree_column.get_sort_order() == gtk.SORT_DESCENDING

        row = model[treeiter]
        if reversed:
            sequence_id = len(model) - row.path[0]
        else:
            sequence_id = row.path[0] + 1
            
        row[COL_MODEL]._kiwi_sequence_id = sequence_id
        
        try:
            renderer.set_property(renderer_prop, sequence_id)
        except TypeError:
            raise TypeError("%r does not support parameter %s" %
                            (renderer, renderer_prop))

class ColoredColumn(Column):
    """
    I am a column which can colorize the text of columns under
    certain circumstances. I take a color and an extra function
    which will be called for each row

    Example, to colorize negative values to red:
    
        >>> def colorize(value):
        ...   return value < 0
        ...
        ... ColoredColumn('age', data_type=int, color='red',
        ...               data_func=colorize),
    """

    def __init__(self, attribute, title=None, data_type=None,
                 color=None, data_func=None, **kwargs):
        if not issubclass(data_type, (int, float)):
            raise TypeError("data type must be int or float")
        if not callable(data_func):
            raise TypeError("data func must be callable")
        
        self._color = gdk.color_parse(color)
        self._color_normal = None
        
        self._data_func = data_func
        
        Column.__init__(self, attribute, title, data_type, **kwargs)

    def on_attach_renderer(self, renderer):
        renderer.set_property('foreground-set', True)
        self._color_normal = renderer.get_property('foreground-gdk')
        
    def renderer_func(self, renderer, data):
        if self._data_func(data):
            color = self._color
        else:
            color = self._color_normal
            
        renderer.set_property('foreground-gdk', color)
            
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

_marker = object()

class List(gtk.ScrolledWindow):
    """An enhanced version of GtkTreeView, which provides pythonic wrappers
    for accessing rows, and optional facilities for column sorting (with
    types) and column selection."""
    
    gsignal('selection-changed', object)
    gsignal('double-click', object)
    gsignal('cell-edited', str, object)

    # this property is used to serialize the columns of a List. The format
    # is a big string with '^' as the column separator and '|' as the field
    # separator
    gproperty('column-definitions', str, nick="ColumnDefinitions")
    gproperty('selection-mode', gtk.SelectionMode,
              default=gtk.SELECTION_BROWSE, nick="SelectionMode")
    
    def __init__(self, columns=[],
                 instance_list=None,
                 mode=gtk.SELECTION_BROWSE):
        """
        @param columns:       a list of L{Column}s
        @param instance_list: a list of objects to be inserted or None
        @param mode:          selection mode
        """
        # allow to specify only one column
        if isinstance(columns, Column):
            columns = [columns]
        elif not isinstance(columns, list):
            raise TypeError("columns must be a list or a Column")

        if not isinstance(mode, gtk.SelectionMode):
            raise TypeError("mode must be an gtk.SelectionMode enum")
        # gtk.SELECTION_EXTENDED & gtk.SELECTION_MULTIPLE are both 3.
        # so we can't do this check.
        #elif mode == gtk.SELECTION_EXTENDED:
        #    raise TypeError("gtk.SELECTION_EXTENDED is deprecated")
        
        gtk.ScrolledWindow.__init__(self)
        # we always want a vertical scrollbar. Otherwise the button on top
        # of it doesn't make sense. This button is used to display the popup
        # menu
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

        # Mapping of instance id -> treeiter
        self._iters = {}
        self._cell_data_caches = {}
        self._columns_configured = False
        self._autosize = True
        self._vscrollbar = None
        
        # by default we are unordered. This index points to the column
        # definition of the column that dictates the order, in case there is
        # any
        self._sort_column_index = -1
        
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
            
        self.show()

    # Python list object implementation
    # These methods makes the kiwi list behave more or less
    # like a normal python list
    #
    # TODO:
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

    # append and remove are below

    def extend(self, iterable):
        """
        Extend list by appending elements from the iterable
        
        @param iteratable:
        """
        
        return self.add_list(iterable, clear=False)

    def index(self, item, start=None, stop=None):
        """
        Return first index of value
        
        @param item:
        @param start:
        @param stop
        """
        
        if start or stop:
            raise NotImplementedError("start and stop")

        treeiter = self._iters.get(id(item), _marker)
        if treeiter is _marker:
            raise ValueError("item %r is not in the list" % item)
        
        return self._model[item.iter].path[0]

    def count(self, item):
        "L.count(item) -> integer -- return number of occurrences of value"

        count = 0
        for row in self._model:
            if row[COL_MODEL] == item:
                count += 1
        return count

    def insert(self, index, item):
        "L.insert(index, item) -- insert object before index"
        raise NotImplementedError
    
    def pop(self, index):
        """
        Remove and return item at index (default last)
        @param index:
        """
        raise NotImplementedError

    def reverse(self, pos, item):
        "L.reverse() -- reverse *IN PLACE*"
        raise NotImplementedError

    def sort(self, pos, item):
        """L.sort(cmp=None, key=None, reverse=False) -- stable sort *IN PLACE*;
        cmp(x, y) -> -1, 0, 1"""
        raise NotImplementedError

    # GObject property handling
    def do_get_property(self, pspec):
        if pspec.name == 'column-definitions':
            return self._columns_string
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
    def _load(self, instances, progress_handler=None):
        # do nothing if empty list or None provided
        if not instances: 
            return

        instances = iter(instances)
        try:
            first = instances.next()
        except StopIteration:
            # Empty list, just give up
            return
        
        if not self._has_enough_type_information():
            self._guess_types(first)
            self._setup_columns()
            
        model = self._model
        iters = self._iters
        iters[id(first)] = model.append((first,))
        
        # In the case of an empty model, select the first instance
        if len(model) == 1:
            self.select(first)

        for instance in instances:
            iters[id(instance)] = model.append((instance,))
            
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
            
        value_type = type(value)
        if value_type is type(None):
            raise TypeError("Detected invalid type None for column `%s'; "
                            "please specify type in Column constructor.""" %
                            column.attribute)
        return value_type
    
    def _setup_columns(self):
        if self._columns_configured:
            return

        searchable = None
        sorted = None
        for column in self._columns:
            if column.searchable:
                if searchable:
                    raise ValueError("Can't make column %s searchable, column"
                                     " %s is already set as searchable" % (
                        column.attribute, searchable.attribute))
                searchable = column.searchable
            elif column.sorted:
                if sorted:
                    raise ValueError("Can't make column %s sorted, column"
                                     " %s is already set as sortable" % (
                        column.attribute, column.sorted))
                sorted = column.sorted

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
        if column.on_attach_renderer:
            column.on_attach_renderer(renderer)
        justify = column.justify
        # If we don't specify a justification, right align it for int/float
        # and left align it for everything else. 
        if justify is None:
            if issubclass(column.data_type, (int, float)):
                justify = gtk.JUSTIFY_RIGHT
            else:
                justify = gtk.JUSTIFY_LEFT
                
        if justify == gtk.JUSTIFY_RIGHT:
            xalign = 1.0
        elif justify == gtk.JUSTIFY_CENTER:
            xalign = 0.5
        elif justify in (gtk.JUSTIFY_LEFT, 
                         gtk.JUSTIFY_FILL):
            xalign = 0.0
        else:
            raise AssertionError
        renderer.set_property("xalign", xalign)
        treeview_column.set_property("alignment", xalign)

        cell_data_func = self._cell_data_func
        if column.cell_data_func:
            cell_data_func = column.cell_data_func
        elif column.cache:
            self._cell_data_caches[column.attribute] = {}
            
        treeview_column.pack_start(renderer)
        treeview_column.set_cell_data_func(renderer, cell_data_func,
                                           (column, renderer_prop,
                                            column.as_string))
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

        if column.searchable:
            if not issubclass(column.data_type, basestring):
                raise TypeError("Unsupported data type for "
                                "searchable column: %s" % column.data_type)
            self._treeview.set_search_column(index)
            self._treeview.set_search_equal_func(self._search_equal_func,
                                                 column)

        if column.radio:
            if not issubclass(column.data_type, bool):
                raise TypeError("You can only use radio for boolean columns")
            
        # typelist here may be none. It's okay; justify_columns will try
        # and use the specified justifications and if not present will
        # not touch the column. When typelist is not set,
        # append/add_list have a chance to fix up the remaining
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
    
    def _on_renderer_toggle__toggled(self, renderer, path, model, attribute):
        # Deactive old one
        old = renderer.get_data('kiwilist::radio-active')
        
        # If we don't have the radio-active set it means we're doing
        # This for the first time, so scan and see which one is currently
        # active, so we can deselect it
        if not old:
            # XXX: Handle multiple values set to True, this
            #      algorithm just takes the first one it finds
            for row in self._model:
                obj = row[COL_MODEL]
                value = getattr(obj, attribute)
                if value == True:
                    old = obj
                    break
            else:
                raise TypeError("You need an initial attribute value set "
                                "to true when using radio")

        setattr(old, attribute, False)

        # Active new and save a reference to the object of the
        # previously selected row
        new = model[path][COL_MODEL]
        setattr(new, attribute, True)
        renderer.set_data('kiwilist::radio-active', new)
        
    def _on_renderer_text__edited(self, renderer, path, text,
                                  model, attribute, column, as_string):
        obj = model[path][COL_MODEL]
        value = as_string(text)
        setattr(obj, attribute, value)
        self.emit('cell-edited', attribute, value)
        
    def _guess_renderer_for_type(self, column):
        """Gusses which CellRenderer we should use for a given type.
        It also set the property of the renderer that depends on the model,
        in the renderer.
        """
        
        # TODO: Move to column
        data_type = column.data_type
        if data_type is bool:
            renderer = gtk.CellRendererToggle()
            if column.radio:
                renderer.set_radio(True)

            if column.editable:
                renderer.set_property('activatable', True)
                renderer.connect('toggled', self._on_renderer_toggle__toggled,
                                 self._model, column.attribute)
                
            prop = 'active'
        elif issubclass(data_type, (datetime.date, datetime.time,
                                  basestring, int, float)):
            renderer = gtk.CellRendererText()
            prop = 'text'
            if column.editable:
                renderer.set_property('editable', True)
                renderer.connect('edited', self._on_renderer_text__edited,
                                 self._model, column.attribute, column,
                                 column.from_string)

        else:
            raise ValueError("the type %s is not supported yet" % data_type)

        return renderer, prop
    
    def _search_equal_func(self, model, tree_column, key, treeiter, column):
        data = column.get_attribute(model[treeiter][COL_MODEL],
                                    column.attribute, None)
        if data.startswith(key):
            return False
        return True
        
    def _cell_data_func(self, tree_column, renderer, model, treeiter,
                        (column, renderer_prop, as_string)):

        row = model[treeiter]
        if column.cache:
            cache = self._cell_data_caches[column.attribute]
            path = row.path[0]
            if path in cache:
                data = cache[path]
            else:
                data = column.get_attribute(row[COL_MODEL],
                                            column.attribute, None)
                cache[path] = data
        else:
            data = column.get_attribute(row[COL_MODEL],
                                        column.attribute, None)

        if column.format:
            text = lformat(column.format, data)
        elif column.format_func:
            text = column.format_func(data)
        elif (column.data_type == datetime.date or
              column.data_type == datetime.datetime or
              column.data_type == datetime.time or
              column.data_type == currency):
            text = as_string(data)
        else:
            text = data
            
        renderer.set_property(renderer_prop, text)

        if column.renderer_func:
            column.renderer_func(renderer, data)
            
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
    def _select_and_focus_row(self, row_iter):
        self._treeview.set_cursor(self._model[row_iter].path)
                    
    def _sort_function(self, model, iter1, iter2):
        column = self._columns[self._sort_column_index]
        attr = column.attribute
        return column.compare(
            column.get_attribute(model[iter1][COL_MODEL], attr),
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
            winx, winy = gdk_window.get_origin()
            self._popup_window.move(winx + old_alloc.x,
                                    winy + old_alloc.y)
        
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
        return self._columns

    def get_column_by_name(self, name):
        """Returns the name of a column"""
        for column in self._columns:
            if column.attribute == name:
                return column

        raise LookupError("There is no column called %s" % name)

    def get_treeview_column(self, column):
        """
        @param column: a @Column
        """
        if not isinstance(column, Column):
            raise TypeError
        
        if not column in self._columns:
            raise ValueError
        
        index = self._columns.index(column)
        tree_columns = self._treeview.get_columns()
        return tree_columns[index]
    
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
                self._columns.append(Column.from_string(col))
        elif isinstance(value, (list, tuple)):
            self._columns = value
            self._columns_string = '^'.join([str(col) for col in value])
        else:
            raise ValueError("value should be a string of a list of columns")

        self._clear_columns()
        if self._has_enough_type_information():
            self._setup_columns()
        
    def append(self, instance, select=False):
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
        self._iters[id(instance)] = row_iter
        
        if self._autosize:
            self._treeview.columns_autosize()

        if select:
            self._select_and_focus_row(row_iter)
        self._treeview.thaw_notify()

    def remove(self, instance):
        """Remove an instance from the list.
        If the instance is not in the list it returns False. Otherwise it
        returns True.
        """
        if not self._has_enough_type_information():
            raise RuntimeError(("There is no columns neither data on the "
                                "list yet so you can not remove any instance"))

        objid = id(instance)
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        
        # linear search for the instance to remove
        treeiter = self._iters.pop(objid)
        if treeiter:
            # Remove any references to this path
            path = self._model[treeiter].path[0]
            for cache in self._cell_data_caches.values():
                if path in cache:
                    del cache[path]

            # All references to the iter gone, now it can be removed
            self._model.remove(treeiter)
                
            return True
            
        return False

    def update(self, instance):
        objid = id(instance)
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]
        self._model.row_changed(self._model[treeiter].path, treeiter)

    def refresh(self):
        """
        Reloads the values from all objects.
        """

        # XXX: Optimize this to only reload items, no need to remove/readd
        model = self._model
        instances = [row[COL_MODEL] for row in model]
        model.clear()
        self.add_list(instances)
        
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

    def select_paths(self, paths):
        """
        Selects a number of rows corresponding to paths
        @param paths:
        """

        selection = self._treeview.get_selection()
        if selection.get_mode() == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed")

        for path in paths:
            selection.select_path(path)

    def select(self, instance, scroll=True):
        objid = id(instance)
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)

        selection = self._treeview.get_selection()
        if selection.get_mode() == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed")

        treeiter = self._iters[objid]
        
        selection.select_iter(treeiter)

        if scroll:
            self._treeview.scroll_to_cell(self._model[treeiter].path,
                                          None, True, 0.5, 0)

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

        model, treeiter = selection.get_selected()
        if treeiter:
            return model[treeiter][COL_MODEL]

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
    
    def add_list(self, instances, clear=True, progress_handler=None):
        """
        Allows a list to be loaded, by default clearing it first.
        freeze() and thaw() are called internally to avoid flashing.
        
        @param instances: a list to be added
        @param clear: a boolean that specifies whether or not to
          clear the list
        @param progress_handler: a callback function to be called
            while the list is being filled
        """

        self._treeview.freeze_notify()

        if clear:
            self.unselect_all()
            self.clear()
            
        ret = self._load(instances, progress_handler)
            
        self._treeview.thaw_notify()
        return ret

    def clear(self):
        """Removes all the instances of the list"""
        self._model.clear()
        self._iters = {}
        
        # Don't clear the whole cache, just the
        # individual column caches
        for key in self._cell_data_caches:
            self._cell_data_caches[key] = {}
        
    def get_next(self, instance):
        """
        Returns the item after instance in the list.
        Note that the instance must be inserted before this can be called
        If there are no instances after,  the first item will be returned.
        
        @param instance: the instance
        """

        objid = id(instance)
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)

        treeiter = self._iters[objid]
        
        model = self._model
        pos = model[treeiter].path[0]
        if pos >= len(model) - 1:
            pos = 0
        else:
            pos += 1
        return model[pos][COL_MODEL]
    
    def get_previous(self, instance=False):
        """
        Returns the item before instance in the list.
        Note that the instance must be inserted before this can be called
        If there are no instances before,  the last item will be returned.
         
        @param instance: the instance
        """
        
        objid = id(instance)
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]
        
        model = self._model
        pos = model[treeiter].path[0]
        if pos == 0:
            pos = len(model) - 1
        else:
            pos -= 1
        return model[pos][COL_MODEL]

    # Backwards compat
    def add_instance(self, *args, **kwargs):
        return self.append(*args, **kwargs)
    add_instance = deprecated('append')(add_instance)

    def remove_instance(self, *args, **kwargs):
        return self.remove(*args, **kwargs)
    remove_instance = deprecated('remove')(remove_instance)

    def update_instance(self, *args, **kwargs):
        return self.update(*args, **kwargs)
    update_instance = deprecated('update')(update_instance)
    
    def select_instance(self, *args, **kwargs):
        return self.select(*args, **kwargs)
    select_instance = deprecated('select')(select_instance)

type_register(List)

class ListLabel(gtk.HBox):
    """I am a subclass of a GtkHBox which you can use if you want
    to vertically align a label with a column
    """
    
    def __init__(self, klist, column, label='', value_format='%s'):
        """
        @param klist:        list to follow
        @type klist:         kiwi.ui.widget.list.List
        @param column:       name of a column in a klist
        @type column:        string
        @param label:        label
        @type label:         string
        @param value_format: format string used to format value
        @type value_format:  string
        """
        self._label = label
        self._label_width = -1
        if not isinstance(klist, List):
            raise TypeError("list must be a kiwi list and not %r" %
                            type(klist).__name__)
        self._klist = klist
        if not isinstance(column, str):
            raise TypeError("column must be a string and not %r" %
                            type(column).__name__)
        self._column = klist.get_column_by_name(column)
        self._value_format = value_format
        
        gtk.HBox.__init__(self)

        self._create_ui()

    # Public API
    
    def set_value(self, value):
        """Sets the value of the label.
        Note that it needs to be of the same type as you specified in
        value_format in the constructor.
        I also support the GMarkup syntax, so you can use "<b>%d</b>" if
        you want."""
        self._value_widget.set_markup(self._value_format % value)

    def get_value_widget(self):
        return self._value_widget

    def get_label_widget(self):
        return self._label_widget
    
    # Private
    
    def _create_ui(self):

        # When tracking the position/size of a column, we need to pay
        # attention to the following two things:
        # * treeview_column::width
        # * size-allocate of treeview_columns header widget
        #
        tree_column = self._klist.get_treeview_column(self._column)
        tree_column.connect('notify::width',
                            self._on_treeview_column__notify_width)
        
        button = self._klist._get_column_button(tree_column)
        button.connect('size-allocate',
                       self._on_treeview_column_button__size_allocate)
        
        self._label_widget = gtk.Label()
        self._label_widget.set_markup(self._label)
        
        layout = self._label_widget.get_layout()
        self._label_width = layout.get_pixel_size()[0]
        self._label_widget.set_alignment(1.0, 0.5)
        self.pack_start(self._label_widget, False, False, padding=6)
        self._label_widget.show()

        self._value_widget = gtk.Label()
        xalign = tree_column.get_property('alignment')
        self._value_widget.set_alignment(xalign, 0.5)
        self.pack_start(self._value_widget, False, False)
        self._value_widget.show()

    def _resize(self, position=-1, width=-1):
        if position != -1:
            if position != 0:
                if self._label_width > position:
                    self._label_widget.set_text('')
                else:
                    self._label_widget.set_markup(self._label)

            # XXX: Replace 12 with a constant
            if position >= 12:
                self._label_widget.set_size_request(position - 12, -1)
                
        if width != -1:
            self._value_widget.set_size_request(width, -1)

    # Callbacks
    
    def _on_treeview_column_button__size_allocate(self, label, rect):
        self._resize(position=rect[0])
             
    def _on_treeview_column__notify_width(self, treeview, pspec):
        value = treeview.get_property(pspec.name)
        self._resize(width=value)

    def _on_list__size_allocate(self, list, rect):
        self._resize(position=rect[0], width=rect[2])
            
        
class SummaryLabel(ListLabel):
    """I am a subclass of ListLabel which you can use if you want
    to summarize all the values of a specific column.
    Please note that I only know how to handle int and float column
    data types and I will complain if you give me something else."""
    
    def __init__(self, klist, column, label=_('Total:'), value_format='%s'):
        ListLabel.__init__(self, klist, column, label, value_format)
        if not issubclass(self._column.data_type, (int, float)):
            raise TypeError("data_type of column must be int or float, not %r",
                            self._column.data_type)
        klist.connect('cell-edited', self._on_klist__cell_edited)
        self.update_total()

    # Public API
    
    def update_total(self):
        """Recalculate the total value of all columns"""
        attr = self._column.attribute
        value = sum([kgetattr(obj, attr) for obj in self._klist], 0.0)
        self.set_value(value)

    # Callbacks
    
    def _on_klist__cell_edited(self, klist, attribute, value):
        self.update_total()

