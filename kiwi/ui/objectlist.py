#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2008 Async Open Source
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
import pickle

import gobject
import pango
import gtk
from gtk import gdk

from kiwi.accessor import kgetattr
from kiwi.datatypes import converter, number, Decimal, ValidationError
from kiwi.currency import currency # after datatypes
from kiwi.enums import Alignment
from kiwi.log import Logger
from kiwi.python import enum, slicerange
from kiwi.utils import gsignal, type_register
from kiwi.ui.widgets.contextmenu import ContextMenu

_ = lambda m: gettext.dgettext('kiwi', m)

log = Logger('objectlist')

def str2enum(value_name, enum_class):
    "converts a string to a enum"
    for _, _enum in enum_class.__enum_values__.items():
        if value_name in (_enum.value_name, _enum.value_nick):
            return _enum

def str2bool(value, from_string=converter.from_string):
    "converts a boolean to a enum"
    return from_string(bool, value)


class Column(gobject.GObject):
    """
    Specifies a column for an L{ObjectList}, see the ObjectList documentation
    for a simple example.

    Properties
    ==========
      - B{title}: string I{mandatory}
        - the title of the column, defaulting to the capitalized form of
          the attribute
      - B{data-type}: object I{str}
        - the type of the attribute that will be inserted into the column.
          Supported data types: bool, int, float, str, unicode,
          decimal.Decimal, datetime.date, datetime.time, datetime.datetime,
          gtk.gdk.Pixbuf, L{kiwi.currency.currency}, L{kiwi.python.enum}.
      - B{visible}: bool I{True}
        - specifying if it is initially hidden or shown.
      - B{justify}: gtk.Justification I{None}
        - one of gtk.JUSTIFY_LEFT, gtk.JUSTIFY_RIGHT or gtk.JUSTIFY_CENTER
          or None. If None, the justification will be determined by the type
          of the attribute value of the first instance to be inserted in the
          ObjectList (for instance numbers will be right-aligned).
      - B{format}: string I{""}
        - a format string to be applied to the attribute value upon insertion
          in the list.
      - B{width}: integer I{65535}
        - the width in pixels of the column, if not set, uses the default to
          ObjectList. If no Column specifies a width, columns_autosize() will
          be called on the ObjectList upon append() or the first add_list().
      - B{sorted}: bool I{False}
        - whether or not the ObjectList is to be sorted by this column.
          If no Columns are sorted, the ObjectList will be created unsorted.
      - B{order}: GtkSortType I{-1}
        - one of gtk.SORT_ASCENDING, gtk.SORT_DESCENDING or -1
          The value -1 is mean that the column is not sorted.
      - B{expand}: bool I{False}
        - if set column will expand. Note: this space is shared equally amongst
          all columns that have the expand set to True.
      - B{tooltip}: string I{""}
        - a string which will be used as a tooltip for the column header
      - B{format_func}: object I{None}
        -  a callable which will be used to format the output of a column.
           The function will take one argument which is the value to convert
           and is expected to return a string.
           I{Note}: that you cannot use format and format_func at the same time,
           if you provide a format function you'll be responsible for
           converting the value to a string.
      - B{format_func_data}: object I{None}
        -  If format_func_data is not None, format_func will receive the row
           object instead of just the column value, and also receive this value
           as a second argument.
      - B{editable}: bool I{False}
        - if true the field is editable and when you modify the contents of
          the cell the model will be updated.
      - B{searchable}: bool I{False}
        - if true the attribute values of the column can be searched using
          type ahead search. Only string attributes are currently supported.
      - B{radio}: bool I{False}
        -  If true render the column as a radio instead of toggle.
           Only applicable for columns with boolean data types.
      - B{spin_adjustment}: gtk.Adjustment I{None}
        -  A gtk.Adjustment instance. If set, render the column cell as
           a spinbutton.
      - B{use_stock}: bool I{False}
        - If true, this will be rendered as pixbuf from the value which
          should be a stock id.
      - B{icon_size}: gtk.IconSize I{gtk.ICON_SIZE_MENU}
      - B{editable_attribute}: string I{""}
        - a string which is the attribute which should decide if the
          cell is editable or not.
      - B{use_markup}: bool I{False}
        - If true, the text will be rendered with markup
      - B{expander}: bool I{False}
        - If True, this column will be used as the tree expander column
      - B{ellipsize}: pango.EllipsizeMode I{pango.ELLIPSIZE_NONE}
        - One of pango.ELLIPSIZE_{NONE, START, MIDDLE or END}, it describes
          where characters should be removed in case ellipsization
          (where to put the ...) is needed.
      - B{font-desc}: str I{""}
        - A string passed to pango.FontDescription, for instance "Sans" or
      - B{column}: str None
        - A string referencing to another column. If this is set a new column
          will not be created and the column will be packed into the other.
      - B{sort_func}: object I{None}
        -  a callable which will be used to sort the contents of the column.
           The function will take two values (x and y) from the column and
           should return negative if x<y, zero if x==y, positive if x>y.
      - B{pack_end}: bool I{False}
        - If set it will pack the renderer to the end of the column instead
          of the beginning.
      - B{width_chars}: int I{-1}
        - If set it will specify the number of characters that should displayed
          for the cells in this column.
    """
    __gtype_name__ = 'Column'
    attribute = gobject.property(type=str,
                                 flags=(gobject.PARAM_READWRITE |
                                        gobject.PARAM_CONSTRUCT_ONLY))
    title = gobject.property(type=str)
    visible = gobject.property(type=bool, default=True)
    justify = gobject.property(type=gtk.Justification, default=gtk.JUSTIFY_LEFT)
    format = gobject.property(type=str)
    width = gobject.property(type=int, maximum=2**16)
    sorted = gobject.property(type=bool, default=False)
    order = gobject.property(type=gtk.SortType, default=gtk.SORT_ASCENDING)
    expand = gobject.property(type=bool, default=False)
    tooltip = gobject.property(type=str)
    format_func = gobject.property(type=object)
    format_func_data = gobject.property(type=object, default=None)
    editable = gobject.property(type=bool, default=False)
    searchable = gobject.property(type=bool, default=False)
    radio = gobject.property(type=bool, default=False)
    spin_adjustment = gobject.property(type=object)
    use_stock = gobject.property(type=bool, default=False)
    use_markup = gobject.property(type=bool, default=False)
    icon_size = gobject.property(type=gtk.IconSize, default=gtk.ICON_SIZE_MENU)
    editable_attribute = gobject.property(type=str)
    expander = gobject.property(type=bool, default=False)
    ellipsize = gobject.property(type=pango.EllipsizeMode, default=pango.ELLIPSIZE_NONE)
    font_desc = gobject.property(type=str)
    column = gobject.property(type=str)
    sort_func = gobject.property(type=object, default=None)
    pack_end = gobject.property(type=bool, default=False)
    width_chars = gobject.property(type=int, default=-1)

    # This can be set in subclasses, to be able to allow custom
    # cell_data_functions, used by SequentialColumn
    cell_data_func = None

    # This is called after the renderer property is set, to allow
    # us to set custom rendering properties
    renderer_func = None

    # This is called when the renderer is created, so we can set/fetch
    # initial properties
    on_attach_renderer = None

    def __init__(self, attribute='', title=None, data_type=None, **kwargs):
        """
        Creates a new Column, which describes how a column in a
        ObjectList should be rendered.

        @param attribute: a string with the name of the instance attribute the
            column represents.
        @param title: the title of the column, defaulting to the capitalized
            form of the attribute.
        @param data_type: the type of the attribute that will be inserted
            into the column.

        @note: title_pixmap: (TODO) if set to a filename a pixmap will be
            used *instead* of the title set. The title string will still be
            used to identify the column in the column selection and in a
            tooltip, if a tooltip is not set.
        """
        # XXX: filter function?
        if ' ' in attribute:
            msg = ("The attribute can not contain spaces, otherwise I can"
                   " not find the value in the instances: %s" % attribute)
            raise AttributeError(msg)

        self._objectlist = None
        self.compare = None
        self.from_string = None

        kwargs['attribute'] = attribute
        kwargs['title'] = title or attribute.capitalize()
        if not data_type:
            data_type = str
        kwargs['data_type'] = data_type

        # If we don't specify a justification, right align it for int/float
        # center for bools and left align it for everything else.
        if "justify" not in kwargs:
            if data_type:
                conv = converter.get_converter(data_type)
                if issubclass(data_type, bool):
                    kwargs['justify'] = gtk.JUSTIFY_CENTER
                elif conv.align == Alignment.RIGHT:
                    kwargs['justify'] = gtk.JUSTIFY_RIGHT

        format_func = kwargs.get('format_func')
        if format_func:
            if not callable(format_func):
                raise TypeError("format_func must be callable")
            if 'format' in kwargs:
                raise TypeError(
                    "format and format_func can not be used at the same time")

        # editable_attribute always turns on editable
        if 'editable_attribute' in kwargs:
            if not kwargs.get('editable', True):
                raise TypeError(
                    "editable cannot be disabled when using editable_attribute")
            kwargs['editable'] = True

        if 'spin_adjustment' in kwargs:
            adjustment = kwargs.get('spin_adjustment')
            if not isinstance(adjustment, gtk.Adjustment):
                raise TypeError(
                    "spin_adjustment must be a gtk.Adjustment instance")

        sort_func = kwargs.get('sort_func')
        if sort_func:
            if not callable(sort_func):
                raise TypeError("sort_func must be callable")
            self.compare = sort_func

        gobject.GObject.__init__(self, **kwargs)

        # It makes sense to set the default ellipsize to end if we have
        # a column which expands so it doesn't end up using more space
        # than there is available
        if not 'ellipsize' in kwargs and self.expand:
            self.ellipsize = pango.ELLIPSIZE_END

    def __repr__(self):
        namespace = self.__dict__.copy()
        return "<%s: %s>" % (self.__class__.__name__, namespace)

    def _get_data_type(self):
        return self._data_type

    def _set_data_type(self, data):
        if data is not None:
            conv = converter.get_converter(data)
            self.compare = self.compare or conv.get_compare_function()
            self.from_string = conv.from_string
        self._data_type = data
    data_type = gobject.property(getter=_get_data_type,
                                 setter=_set_data_type,
                                 type=object)

    def attach(self, objectlist):
        self._objectlist = objectlist

        model = objectlist.get_model()
        # You can't subclass bool, so this is okay
        if (self.data_type is bool and self.format):
            raise TypeError("format is not supported for boolean columns")

        if not self.column:
            treeview_column = gtk.TreeViewColumn()
        else:
            other_column = objectlist.get_column_by_name(self.column)
            treeview_column = objectlist.get_treeview_column(other_column)

        treeview_column.attribute = self.attribute
        renderer, renderer_prop = self.create_renderer(model)
        if self.on_attach_renderer:
            self.on_attach_renderer(renderer)
        justify = self.justify
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

        if self.ellipsize:
            renderer.set_property('ellipsize', self.ellipsize)
        if self.font_desc:
            renderer.set_property('font-desc',
                                  pango.FontDescription(self.font_desc))
        if self.use_stock:
            cell_data_func = self._cell_data_pixbuf_func
        elif issubclass(self.data_type, enum):
            cell_data_func = self._cell_data_combo_func
        elif issubclass(self.data_type, number) and self.spin_adjustment:
            cell_data_func = self._cell_data_spin_func
        else:
            cell_data_func = self._cell_data_text_func

        if self.cell_data_func:
            cell_data_func = self.cell_data_func

        # This is a bit hackish, we should probably
        # add a proper api to determine the expanding of
        # individual cells.
        if self.data_type == gtk.gdk.Pixbuf or self.use_stock:
            expand = False
        else:
            expand = True

        if self.data_type == gtk.gdk.Pixbuf:
            renderer.set_padding(2, 0)

        if self.pack_end:
            treeview_column.pack_end(renderer, expand)
        else:
            treeview_column.pack_start(renderer, expand)

        treeview_column.set_cell_data_func(renderer, cell_data_func,
                                           (self, renderer_prop))
        treeview_column.set_visible(self.visible)

        if self.width:
            treeview_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            treeview_column.set_fixed_width(self.width)

        if self.expand:
            treeview_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            treeview_column.set_expand(True)

        if self.sorted:
            treeview_column.set_sort_indicator(True)

        if self.width:
            self._autosize = False

        if self.radio:
            if not issubclass(self.data_type, bool):
                raise TypeError("You can only use radio for boolean columns")

        if self.spin_adjustment:
            if not issubclass(self.data_type, number):
                raise TypeError("You can only use spin_adjustment for "
                                "number datatypes")

        self.treeview_column = treeview_column

        return treeview_column

    def create_renderer(self, model):
        """Gusses which CellRenderer we should use for a given type.
        It also set the property of the renderer that depends on the model,
        in the renderer.
        """

        data_type = self.data_type
        if data_type is bool:
            renderer = gtk.CellRendererToggle()
            if self.editable:
                renderer.set_property('activatable', True)
                # Boolean can be either a radio or a checkbox.
                # Changes are handled by the toggled callback, which
                # should only be connected if the column is editable.
                if self.radio:
                    renderer.set_radio(True)
                    cb = self._on_renderer_toggle_radio__toggled
                else:
                    cb = self._on_renderer_toggle_check__toggled
                renderer.connect('toggled', cb, model, self.attribute)
            prop = 'active'
        elif self.use_stock or data_type == gdk.Pixbuf:
            renderer = gtk.CellRendererPixbuf()
            prop = 'pixbuf'
            if self.editable:
                raise TypeError("use-stock columns cannot be editable")
        elif issubclass(data_type, enum):
            if data_type is enum:
                raise TypeError("data_type must be a subclass of enum")

            enum_model = gtk.ListStore(str, object)
            items = data_type.names.items()
            items.sort()
            for key, value in items:
                enum_model.append((key.lower().capitalize(), value))

            renderer =  gtk.CellRendererCombo()
            renderer.set_property('model', enum_model)
            renderer.set_property('text-column', 0)
            renderer.set_property('has-entry', True)
            if self.editable:
                renderer.set_property('editable', True)
                renderer.connect('edited', self._on_renderer_combo__edited,
                                 model, self.attribute, self)
            prop = 'model'
        elif issubclass(data_type, number) and self.spin_adjustment:
            renderer = gtk.CellRendererSpin()
            if not self.editable:
                raise TypeError("spin_adjustment columns must be editable")

            renderer.set_property('editable', True)
            renderer.set_property('adjustment', self.spin_adjustment)
            renderer.connect('edited', self._on_renderer_spin__edited,
                             model, self.attribute, self, self.from_string)
            prop = 'text'
        elif issubclass(data_type, (datetime.date, datetime.time,
                                    basestring, number,
                                    currency)):
            renderer = gtk.CellRendererText()
            if self.use_markup:
                prop = 'markup'
            else:
                prop = 'text'
            if self.editable:
                renderer.set_property('editable', True)
                renderer.connect('edited', self._on_renderer_text__edited,
                                 model, self.attribute, self,
                                 self.from_string)
            if self.width_chars != -1:
                renderer.set_property('width-chars', self.width_chars)
        else:
            raise ValueError("the type %s is not supported yet" % data_type)

        return renderer, prop

    # CellRenderers
    def _cell_data_text_func(self, tree_column, renderer, model, treeiter,
                             (column, renderer_prop)):
        "To render the data of a cell renderer text"
        row = model[treeiter]
        if column.editable_attribute:
            data = column.get_attribute(row[COL_MODEL],
                                        column.editable_attribute, None)
            if isinstance(renderer, gtk.CellRendererToggle):
                renderer.set_property('activatable', data)
            elif isinstance(renderer, gtk.CellRendererText):
                renderer.set_property('editable', data)
            else:
                raise AssertionError

        obj = row[COL_MODEL]
        data = column.get_attribute(obj, column.attribute, None)
        text = column.as_string(data, obj)

        if self._objectlist.cell_data_func:
            text = self._objectlist.cell_data_func(self, renderer, obj, text)

        renderer.set_property(renderer_prop, text)

        if column.renderer_func:
            column.renderer_func(renderer, row[COL_MODEL])

    def _cell_data_pixbuf_func(self, tree_column, renderer, model, treeiter,
                               (column, renderer_prop)):
        "To render the data of a cell renderer pixbuf"
        row = model[treeiter]
        data = column.get_attribute(row[COL_MODEL],
                                    column.attribute, None)
        if data is not None:
            pixbuf = self._objectlist.render_icon(data, column.icon_size)
            renderer.set_property(renderer_prop, pixbuf)

    def _cell_data_combo_func(self, tree_column, renderer, model, treeiter,
                              (column, renderer_prop)):
        row = model[treeiter]
        obj = row[COL_MODEL]
        data = column.get_attribute(obj, column.attribute, None)
        text = column.as_string(data, obj)
        renderer.set_property('text', text.lower().capitalize())

    def _cell_data_spin_func(self, tree_column, renderer, model, treeiter,
                             (column, renderer_prop)):
        "To render the data of a cell renderer spin"
        row = model[treeiter]
        if column.editable_attribute:
            data = column.get_attribute(row[COL_MODEL],
                                        column.editable_attribute, None)
            renderer.set_property('editable', data)

        obj = row[COL_MODEL]
        data = column.get_attribute(obj, column.attribute, None)
        text = column.as_string(data, obj)
        renderer.set_property(renderer_prop, text)

        if column.renderer_func:
            column.renderer_func(renderer, row[COL_MODEL])

    def _on_renderer__toggled(self, renderer, path, column):
        setattr(self._model[path][COL_MODEL], column.attribute,
                not renderer.get_active())

    def _on_renderer_toggle_check__toggled(self, renderer, path, model, attr):
        obj = model[path][COL_MODEL]
        value = not getattr(obj, attr, None)
        setattr(obj, attr, value)
        self._objectlist.emit('cell-edited', obj, attr)

    def _on_renderer_toggle_radio__toggled(self, renderer, path, model, attr):
        # Deactive old one
        old = renderer.get_data('kiwilist::radio-active')

        # If we don't have the radio-active set it means we're doing
        # This for the first time, so scan and see which one is currently
        # active, so we can deselect it
        if not old:
            # XXX: Handle multiple values set to True, this
            #      algorithm just takes the first one it finds
            for row in model:
                obj = row[COL_MODEL]
                value = getattr(obj, attr)
                if value == True:
                    old = obj
                    break
        if old:
            setattr(old, attr, False)

        # Active new and save a reference to the object of the
        # previously selected row
        new = model[path][COL_MODEL]
        setattr(new, attr, True)
        renderer.set_data('kiwilist::radio-active', new)
        self._objectlist.emit('cell-edited', new, attr)

    def _on_renderer_text__edited(self, renderer, path, text,
                                  model, attr, column, from_string):
        obj = model[path][COL_MODEL]
        value = from_string(text)
        setattr(obj, attr, value)
        self._objectlist.emit('cell-edited', obj, attr)

    def _on_renderer_spin__edited(self, renderer, path, value,
                                  model, attr, column, from_string):
        obj = model[path][COL_MODEL]
        try:
            value_model = from_string(value)
        except ValidationError:
            return

        setattr(obj, attr, value_model)
        self._objectlist.emit('cell-edited', obj, attr)

    def _on_renderer_combo__edited(self, renderer, path, text,
                                   model, attr, column):
        obj = model[path][COL_MODEL]
        if not text:
            return

        value_model = renderer.get_property('model')
        for row in value_model:
            if row[0] == text:
                value = row[1]
                break
        else:
            raise AssertionError
        setattr(obj, attr, value)
        self._objectlist.emit('cell-edited', obj, attr)

    def _on_renderer__edited(self, renderer, path, value, column):
        data_type = column.data_type
        if data_type in number:
            value = data_type(value)

        # XXX convert new_text to the proper data type
        setattr(self._model[path][COL_MODEL], column.attribute, value)

    # Public API

    # This is meant to be subclassable, we're using kgetattr, as
    # a staticmethod as an optimization, so we can avoid a function call.
    get_attribute = staticmethod(kgetattr)

    def as_string(self, data, obj=None):
        """
        Formats the column as a string that should be renderd into the cell.

        @param data: The column value that will be converted to string.
        @param obj: Necessary only when format_func_data is set. This will make
                    format_func receive I{obj} instead of I{data}
        """
        data_type = self.data_type
        if data is None and data_type != gdk.Pixbuf:
            text = ''
        elif self.format_func:
            if self.format_func_data is not None:
                text = self.format_func(obj, self.format_func_data)
            else:
                text = self.format_func(data)
        elif (self.format or
            data_type == float or
            data_type == Decimal or
            data_type == currency or
            data_type == datetime.date or
            data_type == datetime.datetime or
            data_type == datetime.time or
            issubclass(data_type, enum)):
            conv = converter.get_converter(data_type)
            text = conv.as_string(data, format=self.format or None)
        else:
            text = data

        return text

    def set_spinbutton_precision_digits(self, digits):
        """Set the number of precision digits to be shown in the
        spinbutton.

        @param digits: the number of precision digits to be set in
        spinbutton
        @type digits: int
        """
        if not self.spin_adjustment:
            raise TypeError("You can not set spinbutton precision "
                            "digits for a column without a spinbutton")
        if not isinstance(digits, int):
            raise TypeError("The number of precision digits to be set in "
                            "the spinbutton must be an integer, %s "
                            "found" % type(digits))

        renderer = self.treeview_column.get_cell_renderers()[0]
        renderer.set_property('digits', digits)



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
                       (column, renderer_prop)):
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

class SearchColumn(Column):
    """
    I am a column that should be used in conjunction with
    L{kiwi.ui.search.SearchSlaveDelegate}

    @param long_title: The title to display in the combo for this field.
                       This is usefull if you need to display a small
                       description on the column header, but still want a full
                       description on the advanced search.
    @param valid_values: This should be a list of touples (display value, db
                         value). If provided, then a combo with only this
                         values will be shown, instead of a free text entry.
    @param search_attribute: Use this if the name of the db column that should
                             be searched is different than the attribute of
                             the model.
    """

    def __init__(self, attribute, title=None, data_type=None,
                 long_title=None, valid_values=None, search_attribute=None,
                 **kwargs):
        """
        """
        self.long_title = long_title
        self.valid_values = valid_values
        self.search_attribute = search_attribute
        self.sensitive = True
        Column.__init__(self, attribute, title, data_type, **kwargs)



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
                 color=None, data_func=None, use_data_model=False, **kwargs):
        if not callable(data_func):
            raise TypeError("data func must be callable")

        self._color = None
        if color:
            self._color = gdk.color_parse(color)

        self._color_normal = None

        self._data_func = data_func
        self._use_data_model = use_data_model

        Column.__init__(self, attribute, title, data_type, **kwargs)

    def on_attach_renderer(self, renderer):
        renderer.set_property('foreground-set', True)
        self._color_normal = renderer.get_property('foreground-gdk')

    def renderer_func(self, renderer, data):
        if not self._use_data_model:
            data = self.get_attribute(data, self.attribute, None)

        if self.format_func_data is not None:
            ret = self._data_func(data, self.format_func_data)
        else:
            ret = self._data_func(data)

        if ret and self._color:
            color = self._color
        elif isinstance(ret, gdk.Color):
            color = ret
        else:
            color = self._color_normal

        renderer.set_property('foreground-gdk', color)

class _ContextMenu(gtk.Menu):

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
            if not header_widget:
                continue
            title = header_widget.get_text()
            if not title.strip():
                title = column.attribute.capitalize()

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

        # The width or height of some of the rows might have
        # changed after changing the visibility of the column,
        # so we have to re-measure all the rows, this can be done
        # using row_changed.
        model = self._treeview.get_model()
        for row in model:
            model.row_changed(row.path, row.iter)

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

class ObjectList(gtk.HBox):
    """
    An enhanced version of GtkTreeView, which provides pythonic wrappers
    for accessing rows, and optional facilities for column sorting (with
    types) and column selection.

    Items in an ObjectList is stored in objects. Each row represents an object
    and each column represents an attribute in the object.
    The column description object must be a subclass of L{Column}.
    Simple example

    >>> class Fruit:
    >>>    pass

    >>> apple = Fruit()
    >>> apple.name = 'Apple'
    >>> apple.description = 'Worm house'

    >>> banana = Fruit()
    >>> banana.name = 'Banana'
    >>> banana.description = 'Monkey food'

    >>> fruits = ObjectList([Column('name'),
    >>>                      Column('description')])
    >>> fruits.append(apple)
    >>> fruits.append(banana)

    Signals
    =======
      - B{row-activated} (list, object):
        - Emitted when a row is "activated", eg double clicked or pressing
          enter. See the GtkTreeView documentation for more information
      - B{selection-changed} (list, object):
        - Emitted when the selection changes for the ObjectList
          enter. See the documentation on GtkTreeSelection::changed
          for more information
      - B{double-click} (list, object):
        - Emitted when a row is double-clicked, mostly you want to use
          the row-activated signal instead to be able catch keyboard events.
      - B{right-click} (list, object):
        - Emitted when a row is clicked with the right mouse button.
      - B{cell-edited} (list, object, attribute):
        - Emitted when a cell is edited.
      - B{has-rows} (list, bool):
        - Emitted when the objectlist goes from an empty to a non-empty
          state or vice verse.
      - B{activate-link} (str):
        - Emitted when the a link in a message is clicked on

    Properties
    ==========
      - B{selection-mode}: gtk.SelectionMode I{gtk.SELECTION_BROWSE}
        - Represents the selection-mode of a GtkTreeSelection of a GtkTreeView.
    """

    __gtype_name__ = 'ObjectList'

    # row activated
    gsignal('row-activated', object)

    # selected row(s)
    gsignal('selection-changed', object)

    # row double-clicked
    gsignal('double-click', object)

    # row right-clicked
    gsignal('right-click', object, gtk.gdk.Event)

    # row middle-clicked
    gsignal('middle-click', object, gtk.gdk.Event)

    # edited object, attribute name
    gsignal('cell-edited', object, str)

    # emitted when empty or non-empty status changes
    gsignal('has-rows', bool)

    # emitted when the user sorts a column
    gsignal('sorting-changed', object, gtk.SortType)

    # emitted when the user clicks on a message link
    gsignal('activate-link', str)

    def __init__(self, columns=None,
                 objects=None,
                 mode=gtk.SELECTION_BROWSE,
                 sortable=False,
                 model=None):
        """
        Create a new ObjectList object.
        @param columns:       a list of L{Column}s
        @param objects:       a list of objects to be inserted or None
        @param mode:          selection mode
        @param sortable:      whether the user can sort the list
        @param model:         gtk.TreeModel to use or None to create one
        """
        if columns is None:
            columns = []
        # allow to specify only one column
        if isinstance(columns, Column):
            columns = [columns]
        elif not isinstance(columns, list):
            raise TypeError(
                "columns must be a list or a Column, not %r" % (columns,))

        if not isinstance(mode, gtk.SelectionMode):
            raise TypeError(
                "mode must be an gtk.SelectionMode enum, not %r" % (mode,))
        # gtk.SELECTION_EXTENDED & gtk.SELECTION_MULTIPLE are both 3.
        # so we can't do this check.
        #elif mode == gtk.SELECTION_EXTENDED:
        #    raise TypeError("gtk.SELECTION_EXTENDED is deprecated")

        self._sortable = sortable

        self._columns = []
        # Mapping of instance id -> treeiter
        self._iters = {}
        self._autosize = True
        self._vscrollbar = None
        self._message_label = None
        self.cell_data_func = None

        gtk.HBox.__init__(self)
        # we always want a vertical scrollbar. Otherwise the button on top
        # of it doesn't make sense. This button is used to display the popup
        # menu

        self._sw = gtk.ScrolledWindow()
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self._sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        # This is required for gobject.new to work, since scrolledwindow.add
        # requires valid adjustments and they are for some reason not
        # properly set when using gobject.new.
        self._sw.set_hadjustment(gtk.Adjustment())
        self._sw.set_vadjustment(gtk.Adjustment())
        self.pack_start(self._sw)
        self._sw.show()

        if not model:
            model = gtk.ListStore(object)
        self._model = model
        self._model.connect('row-inserted', self._on_model__row_inserted)
        self._model.connect('row-deleted', self._on_model__row_deleted)
        self._treeview = gtk.TreeView()
        self._treeview.set_model(model)
        self._treeview.connect('button-press-event',
                               self._on_treeview__button_press_event)
        self._treeview.connect_after('row-activated',
                                     self._after_treeview__row_activated)
        self._treeview.set_rules_hint(True)
        self._treeview.show()
        self._sw.add(self._treeview)

        # create a popup menu for showing or hiding columns
        self._popup = _ContextMenu(self._treeview)

        # when setting the column definition the columns are created
        self.set_columns(columns)

        if objects:
            self.add_list(objects, clear=True)

        # Set selection mode last to avoid spurious events
        selection = self._treeview.get_selection()
        selection.connect("changed", self._on_selection__changed)

        # Select the first item if no items are selected
        if mode != gtk.SELECTION_NONE and objects:
            selection.select_iter(self._model[COL_MODEL].iter)

        self.set_selection_mode(mode)
        self._context_menu = None

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
        return bool(self._iters.get(instance, False))

    def __iter__(self):
        "for item in list"
        class ModelIterator:
            def __init__(self):
                self._index = -1

            def __iter__(self):
                return self

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
            model = self._model
            olditem = model[arg][COL_MODEL]
            model[arg] = (item,)

            # Update iterator cache
            iters = self._iters
            iters[item] = model[arg].iter
            del iters[olditem]

        elif isinstance(arg, slice):
            raise NotImplementedError("slices for list are not implemented")
        else:
            raise TypeError("argument arg must be int or gtk.Treeiter,"
                            " not %s" % type(arg))

    # append and remove are below

    def extend(self, iterable):
        """
        Extend list by appending elements from the iterable

        @param iterable:
        """

        return self.add_list(iterable, clear=False)

    def index(self, item, start=None, stop=None):
        """
        Return first index of value

        @param item:
        @param start:
        @param stop
        """

        if start is not None or stop is not None:
            raise NotImplementedError("start and stop")

        treeiter = self._iters.get(item, _marker)
        if treeiter is _marker:
            raise ValueError("item %r is not in the list" % item)

        return self._model[treeiter].path[0]

    def count(self, item):
        "L.count(item) -> integer -- return number of occurrences of value"

        count = 0
        for row in self._model:
            if row[COL_MODEL] == item:
                count += 1
        return count

    def insert(self, index, instance, select=False):
        """Inserts an instance to the list
        @param index: position to insert the instance at
        @param instance: the instance to be added (according to the columns spec)
        @param select: whether or not the new item should appear selected.
        """
        self._treeview.freeze_notify()

        row_iter = self._model.insert(index, (instance,))
        self._iters[instance] = row_iter

        if self._autosize:
            self._treeview.columns_autosize()

        if select:
            self._select_and_focus_row(row_iter)
        self._treeview.thaw_notify()

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

    def sort_by_attribute(self, attribute, order=gtk.SORT_ASCENDING):
        """
        Sort by an attribute in the object model.

        @param attribute: attribute to sort on
        @type attribute: string
        @param order: one of gtk.SORT_ASCENDING, gtk.SORT_DESCENDING
        @type order: gtk.SortType
        """
        def _sort_func(model, iter1, iter2):
            return cmp(
                getattr(model[iter1][0], attribute, None),
                getattr(model[iter2][0], attribute, None))
        unused_sort_col_id = len(self._columns)
        self._model.set_sort_func(unused_sort_col_id, _sort_func)
        self._model.set_sort_column_id(unused_sort_col_id, order)

    def set_context_menu(self, menu):
        """Sets a context-menu (eg, when you right click) for the list.
        @param menu: context menu
        @type menu: ContextMenu
        """

        if not isinstance(menu, ContextMenu):
            raise TypeError
        self._context_menu = menu

    # Properties

    def _get_selection_mode(self):
        return self.get_selection_mode()

    def _set_selection_mode(self, mode):
        self.set_selection_mode(mode)
    selection_mode = gobject.property(getter=_get_selection_mode,
                                      setter=_set_selection_mode,
                                      type=gtk.SelectionMode,
                                      default=gtk.SELECTION_BROWSE,
                                      nick="SelectionMode")


    # Columns handling

    def _load(self, instances, clear):
        # do nothing if empty list or None provided
        model = self._model
        if clear:
            if not instances:
                self.unselect_all()
                self.clear()
                return

        model = self._model
        iters = self._iters

        old_instances = [row[COL_MODEL] for row in model]

        # Save selection
        selected_instances = []
        if old_instances:
            selection = self._treeview.get_selection()
            _, paths = selection.get_selected_rows()
            if paths:
                selected_instances = [model[path][COL_MODEL]
                                          for (path,) in paths]

        iters = self._iters
        prev = None
        # Do not always just clear the list, check if we have the same
        # instances in the list we want to insert and merge in the new
        # items
        if clear:
            for instance in iter(instances):
                objid = instance
                # If the instance is not in the list insert it after
                # the previous inserted object
                if not objid in iters:
                    if prev is None:
                        prev = model.append((instance,))
                    else:
                        prev = model.insert_after(prev, (instance,))
                    iters[objid] = prev
                else:
                    prev = iters[objid]

            # Optimization when we were empty, we wont need to remove anything
            # nor restore selection
            if old_instances:
                # Remove
                objids = [instance for instance in instances]
                for instance in old_instances:
                    objid = instance
                    if objid in objids:
                        continue
                    self._remove(objid)
        else:
            for instance in iter(instances):
                iters[instance] = model.append((instance,))

        # Restore selection
        for instance in selected_instances:
            objid = instance
            if objid in iters:
                selection.select_iter(iters[objid])

        # As soon as we have data for that list, we can autosize it, and
        # we don't want to autosize again, or we may cancel user
        # modifications.
        if self._autosize:
            self._treeview.columns_autosize()
            self._autosize = False

    def _setup_columns(self, columns):
        sorted = None
        expand = False
        for column in columns:
            if column.sorted:
                if sorted:
                    raise ValueError("Can't make column %s sorted, column"
                                     " %s is already set as sortable" % (
                        column.attribute, sorted))
                sorted = column.attribute
            if column.expand:
                expand = True

        self._sortable = self._sortable or bool(sorted)

        for column in columns:
            self._attach_column(column)

        if not expand:
            column = gtk.TreeViewColumn()
            self._treeview.append_column(column)

    def _attach_column(self, column):
        treeview_column = column.attach(self)
        if column.column:
            return

        # we need to set our own widget because otherwise
        # __get_column_button won't work

        label = gtk.Label(column.title)
        label.show()
        treeview_column.set_widget(label)
        treeview_column.set_resizable(True)
        treeview_column.set_clickable(True)
        treeview_column.set_reorderable(True)
        treeview_column.connect('clicked', self._after_treeview_column__clicked,
                                column)
        self._treeview.append_column(treeview_column)

        # setup the button to show the popup menu
        button = self._get_column_button(treeview_column)
        button.connect('button-release-event',
                       self._on_treeview_header__button_release_event)

        index = self._columns.index(column)
        if self._sortable:
            self._model.set_sort_func(index,
                                      self._model_sort_func,
                                      (column, column.attribute))
            treeview_column.set_sort_column_id(index)

        if column.sorted:
            self._model.set_sort_column_id(index, column.order)

        if column.searchable:
            if not issubclass(column.data_type, basestring):
                raise TypeError("Unsupported data type for "
                                "searchable column: %s" % column.data_type)
            self._treeview.set_search_column(index)
            self._treeview.set_search_equal_func(
                self._treeview_search_equal_func, column)

        if column.tooltip:
            widget = self._get_column_button(treeview_column)
            if widget is not None:
                widget.set_tooltip_text(column.tooltip)

        if column.expander:
            self._treeview.set_expander_column(treeview_column)

    # selection methods
    def _select_and_focus_row(self, row_iter):
        self._treeview.set_cursor(self._model[row_iter].path)

    # handlers & callbacks

    # Model
    def _on_model__row_inserted(self, model, path, iter):
        if len(model) == 1:
            self.emit('has-rows', True)

    def _on_model__row_deleted(self, model, path):
        if not len(model):
            self.emit('has-rows', False)

    def _model_sort_func(self, model, iter1, iter2, (column, attr)):
        "This method is used to sort the GtkTreeModel"
        return column.compare(
            column.get_attribute(model[iter1][COL_MODEL], attr),
            column.get_attribute(model[iter2][COL_MODEL], attr))

    # Selection
    def _on_selection__changed(self, selection):
        "This method is used to proxy selection::changed to selection-changed"
        mode = selection.get_mode()
        if mode == gtk.SELECTION_MULTIPLE:
            item = self.get_selected_rows()
        elif mode in (gtk.SELECTION_SINGLE, gtk.SELECTION_BROWSE):
            item = self.get_selected()
        else:
            raise AssertionError
        self.emit('selection-changed', item)

    # ScrolledWindow
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

    # TreeView
    def _treeview_search_equal_func(self, model, tree_column, key, treeiter, column):
        "for searching inside the treeview, case-insensitive by default"
        data = column.get_attribute(model[treeiter][COL_MODEL],
                                    column.attribute, None)
        if data.lower().startswith(key.lower()):
            return False
        return True

    def _on_treeview_header__button_release_event(self, button, event):
        if event.button == 3:
            self._popup.popup(event)

        return False

    def _after_treeview__row_activated(self, treeview, path, view_column):
        "After activated (double clicked or pressed enter) on a row"
        try:
            row = self._model[path]
        except IndexError:
            print 'path %s was not found in model: %s' % (
                path, map(list, self._model))
            return
        item = row[COL_MODEL]
        self.emit('row-activated', item)

    def _get_selection_or_selected_rows(self):
        selection = self._treeview.get_selection()
        mode = selection.get_mode()
        if mode == gtk.SELECTION_MULTIPLE:
            item = self.get_selected_rows()
        elif mode == gtk.SELECTION_NONE:
            return
        else:
            item = self.get_selected()
        return item

    def _emit_button_press_signal(self, signal_name, event):
        item = self._get_selection_or_selected_rows()
        if item:
            self.emit(signal_name, item, event)

    def _on_treeview__button_press_event(self, treeview, event):
        "Generic button-press-event handler to be able to catch double clicks"

        # Right and Middle click
        if event.type == gtk.gdk.BUTTON_PRESS:
            if event.button == 3:
                signal_name = 'right-click'
                if self._context_menu:
                    self._context_menu.popup(event.button, event.time)
            elif event.button == 2:
                signal_name = 'middle-click'
            else:
                return
            gobject.idle_add(self._emit_button_press_signal, signal_name,
                             event.copy())
        # Double left click
        elif event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            item = self._get_selection_or_selected_rows()
            if item:
                self.emit('double-click', item)


    def _on_treeview__source_drag_data_get(self, treeview, context,
                                           selection, info, timestamp):
        item = self.get_selected()
        selection.set('OBJECTLIST_ROW', 8, pickle.dumps(item))

    def _after_treeview_column__clicked(self, treeview_column, column):
        self.emit('sorting-changed', column.attribute,
                  treeview_column.get_sort_order())

    # Message label

    def _on_message_label__activate_link(self, label, uri):
        self.emit('activate-link', uri)
        return True

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

    # end of the popup button hack

    def _expand_parents(self, treeiter):
        # We need to expand all parent rows before selecting
        row = self._model[treeiter]
        while row.parent:
            self._treeview.expand_row(row.parent.path, True)
            row = row.parent

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
        Get the treeview column given an objectlist column
        @param column: a @Column
        """
        if not isinstance(column, Column):
            raise TypeError

        if not column in self._columns:
            raise ValueError

        return column.treeview_column

    def set_spinbutton_digits(self, column_name, digits):
        """Set the number of precision digits used by the spinbutton in
        a column.

        @param column_name: the column name which has the spinbutton
        @type column_name: str
        @param digits: a number specifying the precision digits
        @type digits: int
        """
        column = self.get_column_by_name(column_name)
        column.set_spinbutton_precision_digits(digits)

    def grab_focus(self):
        """
        Grabs the focus of the ObjectList
        """
        self._treeview.grab_focus()

    def _clear_columns(self):
        # Reset the sort function for all model columns
        model = self._model
        for i, column in enumerate(self._columns):
            # Bug in PyGTK, it should be possible to remove a sort func.
            model.set_sort_func(i, lambda m, i1, i2: -1)

        # Remove all columns
        treeview = self._treeview
        while treeview.get_columns():
            treeview.remove_column(treeview.get_column(0))

        self._popup.clean()
        self._columns = []

    def set_columns(self, columns):
        """
        Set columns.
        @param columns: a sequence of L{Column} objects.
        """

        if not isinstance(columns, (list, tuple)):
            raise ValueError("columns must be a list or a tuple")

        self._clear_columns()
        self._columns = columns
        self._setup_columns(columns)

    def append(self, instance, select=False):
        """Adds an instance to the list.
        @param instance: the instance to be added (according to the columns spec)
        @param select: whether or not the new item should appear selected.
        """

        # Freeze and save original selection mode to avoid blinking
        self._treeview.freeze_notify()

        row_iter = self._model.append((instance,))
        self._iters[instance] = row_iter

        if self._autosize:
            self._treeview.columns_autosize()

        if select:
            self._select_and_focus_row(row_iter)
        self._treeview.thaw_notify()

    def _remove(self, objid):
        # linear search for the instance to remove
        treeiter = self._iters.pop(objid)
        if not treeiter:
            return False

        # All references to the iter gone, now it can be removed
        self._model.remove(treeiter)

        return True

    def remove(self, instance, select=False):
        """Remove an instance from the list.
        If the instance is not in the list it returns False. Otherwise it
        returns True.

        @param instance:
        @param select: if true, the previous item will be selected
          if there is one.
        """

        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)


        if select:
            prev = self.get_previous(instance)
            rv = self._remove(objid)
            if prev != instance:
                self.select(prev)
        else:
            rv = self._remove(objid)
        return rv

    def update(self, instance):
        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]
        self._model.row_changed(self._model[treeiter].path, treeiter)

    def refresh(self, view_only=False):
        """
        Reloads the values from all objects.

        @param view_only: if True, only force a refresh of the
            visible part of this objectlist's Treeview.
        """
        self.clear_message()
        if view_only:
            self._treeview.queue_draw()
        else:
            self._model.foreach(gtk.TreeModel.row_changed)

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

        @param paths: rows to be selected
        """

        selection = self._treeview.get_selection()
        if selection.get_mode() == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed")

        selection.unselect_all()
        for path in paths:
            self._expand_parents(self._model[path].iter)
            selection.select_path(path)

    def select(self, instances, scroll=True):
        if type(instances) not in [list, tuple]:
            instances = [instances]

        if not instances:
            return

        selection = self._treeview.get_selection()
        if selection.get_mode() == gtk.SELECTION_NONE:
            raise TypeError("Selection not allowed")

        if (selection.get_mode() != gtk.SELECTION_MULTIPLE and
            len(instances) > 1):
            raise TypeError("You can only select multiple items with"
                            "selection mode set to gtk.SELECTION_MULTIPLE")

        for instance in instances:
            if not instance in self._iters:
                raise ValueError("instance %s is not in the list" % repr(instance))

            treeiter = self._iters[instance]
            self._expand_parents(treeiter)
            selection.select_iter(treeiter)

        self._select_and_focus_row(treeiter)

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
            log.warn('get_selected() called when multiple rows '
                     'can be selected')

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
            log.warn('get_selected_rows() called when only a single row '
                     'can be selected')

        model, paths = selection.get_selected_rows()
        if paths:
            return [model[path][COL_MODEL] for (path,) in paths]
        return []

    def add_list(self, instances, clear=True):
        """
        Allows a list to be loaded, by default clearing it first.
        freeze() and thaw() are called internally to avoid flashing.

        @param instances: a list to be added
        @param clear: a boolean that specifies whether or not to
          clear the list
        """

        self._treeview.freeze_notify()

        ret = self._load(instances, clear)

        self._treeview.thaw_notify()

        return ret

    def clear(self):
        """Removes all the instances of the list"""
        self._model.clear()
        self._iters = {}
        self.clear_message()

    def get_next(self, instance):
        """
        Returns the item after instance in the list.
        Note that the instance must be inserted before this can be called
        If there are no instances after,  the first item will be returned.

        @param instance: the instance
        """

        objid = instance
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

    def get_previous(self, instance):
        """
        Returns the item before instance in the list.
        Note that the instance must be inserted before this can be called
        If there are no instances before,  the last item will be returned.

        @param instance: the instance
        """

        objid = instance
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

    def get_selected_row_number(self):
        """
        Get the selected row number or None if no rows were selected
        """
        selection = self._treeview.get_selection()
        if selection.get_mode() == gtk.SELECTION_MULTIPLE:
            model, paths = selection.get_selected_rows()
            if paths:
                return paths[0][0]
        else:
            model, iter = selection.get_selected()
            if iter:
                return model[iter].path[0]

    def double_click(self, rowno):
        """
        Same as double clicking on the row rowno

        @param rowno: integer
        """
        columns = self._treeview.get_columns()
        if not columns:
            raise AssertionError(
                "%s has no columns" % self.get_name())

        self._treeview.row_activated(rowno, columns[0])

    def set_headers_visible(self, value):
        """
        Show or hide the headers.
        @param value: if true, shows the headers, if false hide then
        """
        self._treeview.set_headers_visible(value)

    def set_visible_rows(self, rows):
        """
        Sets the number of visible rows of the treeview. This is useful to use
        instead of set_size_request() directly, since you can avoid using raw
        pixel sizes.
        @param rows: number of rows to show
        """

        treeview = self._treeview
        if treeview.get_headers_visible():
            treeview.realize()
            header_h = self._get_header_height()
        else:
            header_h = 0

        column = treeview.get_columns()[0]
        h = column.cell_get_size()[-1]

        focus_padding = treeview.style_get_property('focus-line-width') * 2
        treeview.set_size_request(-1, header_h + (rows * (h + focus_padding)))

    def enable_dnd(self):
        """
        Enables Drag and Drop from this object list
        """
        self._treeview.connect('drag-data-get',
                               self._on_treeview__source_drag_data_get)
        self._treeview.drag_source_set(
            gtk.gdk.BUTTON1_MASK, self.get_dnd_targets(),
            gtk.gdk.ACTION_LINK)

    def get_dnd_targets(self):
        """
        Get a list of dnd targets ObjectList supports
        """
        return [
            ('OBJECTLIST_ROW', 0, 10),
            ]

    def set_message(self, markup):
        """Adds a message on top of the treeview rows
        @markup: PangoMarkup with the text to add
        """

        if self._message_label is None:
            self._viewport = gtk.Viewport()
            self._viewport.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            self.pack_start(self._viewport)

            self._message_box = gtk.EventBox()
            self._message_box.modify_bg(
                gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
            self._viewport.add(self._message_box)
            self._message_box.show()

            self._message_label = gtk.Label()
            self._message_label.connect(
                'activate-link', self._on_message_label__activate_link)
            self._message_label.set_use_markup(True)
            self._message_label.set_alignment(0, 0)
            self._message_label.set_padding(12, 12)
            self._message_box.add(self._message_label)
            self._message_label.show()

        self._sw.hide()
        self._viewport.show()
        self._message_label.set_label(markup)

    def clear_message(self):
        if self._message_label is None:
            return
        self._sw.show()
        self._viewport.hide()
        self._message_label.set_label("")

    def set_cell_data_func(self, cell_data_func):
        self.cell_data_func = cell_data_func

type_register(ObjectList)


class ObjectTree(ObjectList):
    """
    Signals
    =======
      - B{row-expanded} (list, object):
        - Emitted when a row is "expanded", eg the littler arrow to the left
          is opened. See the GtkTreeView documentation for more information.
    """
    __gtype_name__ = 'ObjectTree'

    gsignal('row-expanded', object)

    def __init__(self, columns=[], objects=None, mode=gtk.SELECTION_BROWSE,
                 sortable=False, model=None):
        if not model:
            model = gtk.TreeStore(object)
        ObjectList.__init__(self, columns, objects, mode, sortable, model)
        self.get_treeview().connect('row-expanded', self._on_treeview__row_expanded)

    def __iter__(self):
        # FIXME: This should be sorted in the order the objects are displayed
        return self._iters.iterkeys()

    def _append_internal(self, parent, instance, select, prepend):
        iters = self._iters
        parent_id = parent
        if parent_id in iters:
            parent_iter = iters[parent_id]
        elif parent is None:
            parent_iter = None
        else:
            raise TypeError(
                "parent must be an Object, ObjectRow or None")

        # Freeze and save original selection mode to avoid blinking
        self._treeview.freeze_notify()

        if prepend:
            row_iter = self._model.prepend(parent_iter, (instance,))
        else:
            row_iter = self._model.append(parent_iter, (instance,))

        self._iters[instance] = row_iter

        if self._autosize:
            self._treeview.columns_autosize()

        if select:
            self._select_and_focus_row(row_iter)
        self._treeview.thaw_notify()
        return instance

    def append(self, parent, instance, select=False):
        """
        Append the selected row in an instance.
        @param parent: Object or None, representing the parent
        @param instance: the instance to be added
        @param select: select the row
        @returns: the appended object
        """
        return self._append_internal(parent, instance, select, prepend=False)

    def prepend(self, parent, instance, select=False):
        """
        Prepend the selected row in an instance.
        @param parent: Object or None, representing the parent
        @param instance: the instance to be added
        @param select: select the row
        @returns: the prepended object
        """
        return self._append_internal(parent, instance, select, prepend=True)

    def expand(self, instance, open_all=True):
        """
        This method opens the row specified by path so its children
        are visible.
        @param instance: an instance to expand at
        @param open_all: If True, expand all rows, otherwise just the
        immediate children
        """
        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]

        self.get_treeview().expand_row(
            self._model[treeiter].path, open_all)

    def collapse(self, instance):
        """
        This method collapses the row specified by path
        (hides its child rows, if they exist).
        @param instance: an instance to collapse
        """
        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]

        self.get_treeview().collapse_row(
            self._model[treeiter].path)

    def get_parent(self, instance):
        """
        This method returns the parent of the specified instance
        are visible.
        @returns: the parent of the instance or None
        """
        if instance is None:
            return None
        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)
        treeiter = self._iters[objid]
        parentiter = self._model.iter_parent(treeiter)
        if not parentiter:
            return None

        return self._model[parentiter][COL_MODEL]

    def get_root(self, instance):
        """
        This method returns the root object of a certain instance. If
        the instance is the root, then returns the given instance.
        @param instance: an instance which we want the root object
        """
        # Short-cut for simplified logic for callsites
        if instance is None:
            return None
        objid = instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % instance)

        instance_iter = self._iters[objid]
        if self._model.iter_depth(instance_iter) == 0:
            return self._model[instance_iter][COL_MODEL]

        for iter in self._iters.values():
            if self._model.is_ancestor(iter, instance_iter):
                return self.get_root(self._model[iter][COL_MODEL])

    def get_descendants(self, root_instance):
        """
        This method returns the descendants objects of a certain instance.
        If the given instance is a leaf, then return an empty sequence.
        @param root_instance: an instance which we want the descendants
        @returns: a sequence of descendants objects
        """
        objid = root_instance
        if not objid in self._iters:
            raise ValueError("instance %r is not in the list" % root_instance)

        root_instance_iter = self._iters[objid]
        children = []
        for iter in self._iters.values():
            if self._model.is_ancestor(root_instance_iter, iter):
                children.append(self._model[iter][COL_MODEL])
        return children

    def _on_treeview__row_expanded(self, treeview, treeiter, treepath):
        self.emit('row-expanded', self.get_model()[treeiter][COL_MODEL])

    def flush(self):
        """Update all iterators"""
        def flattern(row):
            self._iters[row[COL_MODEL]] = row.iter
            for child_row in row.iterchildren():
                flattern(child_row)

        for row in self._model:
            flattern(row)

type_register(ObjectTree)

class ListLabel(gtk.HBox):
    """I am a subclass of a GtkHBox which you can use if you want
    to vertically align a label with a column
    """

    def __init__(self, klist, column, label='', value_format='%s',
                 font_desc=None):
        """
        Constructor.
        @param klist:        list to follow
        @type klist:         kiwi.ui.objectlist.ObjectList
        @param column:       name of a column in a klist
        @type column:        string
        @param label:        label
        @type label:         string
        @param value_format: format string used to format value
        @type value_format:  string
        """
        self._label = label
        self._label_width = -1
        if not isinstance(klist, ObjectList):
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

        if font_desc:
            self._value_widget.modify_font(font_desc)
            self._label_widget.modify_font(font_desc)

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
        self.pack_start(self._label_widget, True, True, padding=6)
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
            #if position >= 12:
            #    self._label_widget.set_size_request(position - 12, -1)

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
    Please note that I only know how to handle number column
    data types and I will complain if you give me something else."""

    def __init__(self, klist, column, label=_('Total:'), value_format='%s',
                 font_desc=None):
        ListLabel.__init__(self, klist, column, label, value_format, font_desc)
        if not issubclass(self._column.data_type, number):
            raise TypeError("data_type of column must be a number, not %r",
                            self._column.data_type)
        klist.connect('cell-edited', self._on_klist__cell_edited)
        self.update_total()

    # Public API

    def update_total(self):
        """Recalculate the total value of all columns"""
        column = self._column
        attr = column.attribute
        get_attribute = column.get_attribute

        value = sum([get_attribute(obj, attr, 0) or 0 for obj in self._klist],
                    column.data_type('0'))

        self.set_value(column.as_string(value))

    # Callbacks

    def _on_klist__cell_edited(self, klist, object, attribute):
        self.update_total()
