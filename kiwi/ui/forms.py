# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Outc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""
Form is a simple way of creating fields that are:
  label + proxy widget + button abstraction

"""

import datetime
from decimal import Decimal
import gettext
import math
import sys

import gobject
import gtk

from kiwi.currency import currency
from kiwi.interfaces import IProxyWidget
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.colorbutton import ProxyColorButton
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox
from kiwi.ui.widgets.entry import ProxyEntry, ProxyDateEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.utils import gsignal

_ = lambda m: gettext.dgettext('kiwi', m)


class Field(gobject.GObject):

    #: This is used to sort class variables in creation order
    #: which is essentially the same thing as the order in the
    #: source file, idea borrowed from Django
    global_sort_key = 0

    #: Used by proxy_widgets
    data_type = gobject.property(type=object)

    #: Used by proxy_widgets
    mandatory = gobject.property(type=bool, default=False)

    #: Text of the label that will be next to the field,
    #: Can be None for not displaying any label at all
    label = gobject.property(type=str)

    #: Name of the label widget inside the view, None
    #: means it should be model_attribute + '_lbl'
    label_attribute = gobject.property(type=str)

    #: If we should add an add button next to the widget
    has_add_button = gobject.property(type=bool, default=False)

    #: If we should add an edit button next to the widget
    has_edit_button = gobject.property(type=bool, default=False)

    #: If we should add a delete button next to the widget
    has_delete_button = gobject.property(type=bool, default=False)

    #: If this field should be added to a proxy
    proxy = gobject.property(type=bool, default=False)

    #: When attaching this field to a form, span that much on the
    #: table. Analogous to html columns' colspan property
    colspan = gobject.property(type=int, default=1)

    #: This can be used by subclasses to override the default
    #: values for properties
    default_overrides = {}

    def __init__(self, label='', **kwargs):
        self.model_attribute = None

        # Widgets
        self.label_widget = None
        self.widget = None
        self.add_button = None
        self.edit_button = None
        self.delete_button = None

        # Label is a positional argument for convienience, convert it to
        # a keyword argument so it can be set via GObject.__init__
        kwargs['label'] = label
        for key, value in self.default_overrides.items():
            if key not in kwargs:
                kwargs[key] = value
        gobject.GObject.__init__(self, **kwargs)

        self.sort_key = Field.global_sort_key
        Field.global_sort_key += 1

    @property
    def value(self):
        return getattr(self.view.model, self.model_attribute)

    @property
    def toplevel(self):
        if self.form:
            return self.form.main_view

    def attach_form(self, form, model_attribute):
        self.label_widget = self.build_label()
        self.widget = self.build_widget()
        if IProxyWidget.providedBy(self.widget):
            if self.widget_data_type is not None:
                self.widget.data_type = self.widget_data_type
            self.widget.mandatory = self.mandatory
            self.widget.model_attribute = model_attribute
            if not self.label_attribute:
                self.label_attribute = model_attribute + '_lbl'
            self.widget.connect(
                'content-changed', self._on_widget__content_changed)
        self.model_attribute = model_attribute
        self.form = form
        self.view = form.view
        self._build_add_button()
        self._build_edit_button()
        self._build_delete_button()
        self.attach()
        if self.label_widget:
            self.label_widget.show()
        self.widget.show()

    def _build_add_button(self):
        if not self.has_add_button:
            return

        self.add_button = self.create_button(gtk.STOCK_ADD)
        self.add_button.set_use_stock(True)
        self.add_button.set_tooltip_text(_("Add a %s") % (
            self.label.lower(), ))
        self.add_button.connect('clicked', self.add_button_clicked)

    def _build_edit_button(self):
        if not self.has_edit_button:
            return

        self.edit_button = self.create_button(gtk.STOCK_EDIT)
        self.edit_button.connect('clicked', self.edit_button_clicked)
        self.edit_button.set_use_stock(True)
        self.edit_button.set_tooltip_text(_("Edit the selected %s") % (
            self.label.lower(), ))
        self.edit_button.set_sensitive(False)

    def _build_delete_button(self):
        if not self.has_delete_button:
            return

        self.delete_button = self.create_button(gtk.STOCK_DELETE)
        self.delete_button.connect('clicked', self.delete_button_clicked)
        self.delete_button.set_use_stock(True)
        self.delete_button.set_tooltip_text(_("Delete the selected %s") % (
            self.label.lower(), ))
        self.delete_button.set_sensitive(False)

    def _on_widget__content_changed(self, widget):
        self.content_changed()

    # Public API

    def create_button(self, stock_id):
        button = gtk.Button()
        image = gtk.image_new_from_stock(
            stock_id, gtk.ICON_SIZE_MENU)
        button.set_image(image)
        image.show()
        button.set_relief(gtk.RELIEF_NONE)
        button.show()
        return button

    def set_sensitive(self, value):
        self.widget.set_sensitive(value)
        if self.add_button:
            self.add_button.set_sensitive(value)
        if self.edit_button:
            self.edit_button.set_sensitive(value)
        if self.delete_button:
            self.delete_button.set_sensitive(value)

    # Overridables

    def build_label(self):
        # This method will be overridden by some fields that don't need a
        # label_widget, because they carry their own label. Because of this,
        # we need to verify if label_widget exists everytime we use it.
        label_widget = ProxyLabel()
        if self.label:
            label_widget.set_markup(self.label + ':')
        label_widget.set_alignment(1.0, 0.5)
        return label_widget

    def get_attachable_widget(self):
        """Returns the widget that should be attached in the form

        Subclasses can overwrite this if they need to create a parent container
        for the widget (Like a gtk.ScrolledWindow)
        """
        return self.widget

    def build_widget(self):
        raise NotImplementedError

    def attach(self):
        pass

    def populate(self, value, *args):
        pass

    def add_button_clicked(self, button):
        raise NotImplementedError

    def edit_button_clicked(self, button):
        raise NotImplementedError

    def delete_button_clicked(self, button):
        raise NotImplementedError

    def content_changed(self):
        pass

gobject.type_register(Field)


class EmptyField(Field):
    """
    I am a field representing an empty space,
    rendered as an empty label.
    """

    def build_widget(self):
        return gtk.Label('')

    def build_label(self):
        return None


class BoolField(Field):
    """
    I am a field representing a yes/no choice,
    rendered as a check button.
    """
    widget_data_type = bool

    def build_widget(self):
        widget = ProxyCheckButton(self.label)
        return widget

    def build_label(self):
        return None

gobject.type_register(BoolField)


class TextField(Field):
    """
    I am a text field with one line, editable by the user,
    rendered as an entry.
    """
    editable = gobject.property(type=bool, default=True)
    input_mask = gobject.property(type=object)
    max_length = gobject.property(type=int, default=0)
    widget_data_type = unicode

    def build_widget(self):
        if self.editable:
            widget = ProxyEntry()
            if self.max_length != 0:
                widget.set_width_chars(self.max_length)
            if self.input_mask:
                widget.set_mask(self.input_mask)
        else:
            widget = ProxyLabel()
            # This label should be left aligned.
            widget.set_alignment(0, 0.5)

        return widget

gobject.type_register(TextField)


class PasswordField(TextField):
    """
    I am a password field with one line, editable by the user,
    rendered as an entry with invisible characters.
    """
    def build_widget(self):
        widget = TextField.build_widget(self)
        if self.editable:
            widget.set_visibility(False)

        return widget

gobject.type_register(PasswordField)


class IntegerField(Field):
    """
    I am a numeric field with one line, editable by the user,
    rendered as an entry that allows only integer numbers
    """

    widget_data_type = int

    def build_widget(self):
        widget = ProxyEntry()
        return widget

gobject.type_register(IntegerField)


class ChoiceField(Field):
    """
    I am a field representing a set of choices,
    rendered as a ComboBox or ComboEntry.
    """
    values = gobject.property(type=object)
    use_entry = gobject.property(type=bool, default=False)
    widget_data_type = object

    def build_widget(self):
        if self.use_entry:
            combo = ProxyComboEntry()
        else:
            combo = ProxyComboBox()
        self.fill(combo)
        return combo

    def fill(self, widget):
        if self.values:
            widget.prefill(self.values)

gobject.type_register(ChoiceField)


class PriceField(Field):
    """
    I am a field representing a price, contain a currency symbol,
    right-aligned etc, rendered as an entry.
    """
    widget_data_type = currency

    def build_widget(self):
        entry = ProxyEntry()
        return entry

gobject.type_register(PriceField)


class DateField(Field):
    """
    I am a field representing a date where the user can chose
    a date from a calendar, rendered as a date entry.
    """
    widget_data_type = datetime.date

    def build_widget(self):
        dateentry = ProxyDateEntry()
        return dateentry

gobject.type_register(DateField)


class ColorField(Field):
    """
    I am a field representing a color,
    rendered as a color button.
    """
    widget_data_type = unicode

    def build_widget(self):
        button = ProxyColorButton()
        return button

gobject.type_register(ColorField)


class NumericField(Field):
    """
    I am a field representing a numeric value,
    rendered as a spin button.
    """
    widget_data_type = Decimal

    def build_widget(self):
        entry = ProxySpinButton()
        entry.set_adjustment(gtk.Adjustment(lower=0, step_incr=1,
                                            upper=sys.maxint, page_incr=10))
        return entry

gobject.type_register(NumericField)


class PercentageField(Field):
    """
    I am a field representing a percentage,
    rendered as a spin button.
    """
    widget_data_type = Decimal

    def build_widget(self):
        entry = ProxySpinButton()
        entry.set_adjustment(gtk.Adjustment(lower=0, step_incr=1,
                                            upper=100, page_incr=10))
        entry.set_range(0, 100)
        entry.set_digits(2)
        return entry

gobject.type_register(PercentageField)


class MultiLineField(Field):
    """
    I am a text field with multiple lines,
    rendered as a text view.
    """
    widget_data_type = unicode

    def build_widget(self):
        from kiwi.ui.widgets.textview import ProxyTextView
        widget = ProxyTextView()
        widget.set_wrap_mode(gtk.WRAP_WORD)
        return widget

    def get_attachable_widget(self):
        sw = gtk.ScrolledWindow()
        sw.add(self.widget)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_OUT)
        sw.show()
        return sw

gobject.type_register(MultiLineField)


class FormLayout(object):
    #
    # A Layout is a class that decides how the widgets
    # should be created and put on screen, it needs to:
    # * call form.build_field(field, field_name) for all fields
    #   that are passed into the constructor
    # * pack the following widgets:
    #   * field.label_widget (can be None, for BoolFields for example)
    #   * field.widget
    #   * field.add_button (can be None)
    #   * field.edit_button (can be None)
    #   * field.delete_button (can be None)
    # * setup focus
    # * save the toplevel container as self.widget
    #
    def __init__(self, form, fields):
        self.form = form
        self.fields = fields


class FormTableLayout(FormLayout):
    """Most common layout, a table with columns:

    +-------+-------+---+----+------+
    | Value:|Widget |Add|Edit|Delete|
    +-------+-------+---+----+------+
    |  Name:|Widget |Add|Edit|Delete|
    +-------+-------+---+----+------+
    | ....  |...... |...|....|......|

    Each new field is added as another vertical line.
    Widget will always be visible.
    Add, Edit, Delete are optional.
    Value label can be hidden.
    """

    #: 3 is the number of items - [label]|[widget]|[add|edit|delete]
    COLUMNS_PER_FIELD = 3

    def __init__(self, form, fields, columns=1):
        FormLayout.__init__(self, form, fields)

        # This is the number of spaces we need to be available on the table.
        # Each field will need the same space as its colspan attribute
        required_spaces = sum([f.colspan for f, fname in fields])

        # The number of rows is the relation between required_spaces and
        # columns. Some examples:
        #   10 required_spaces, 1 column = 10 rows (10 x 1 = 10 spaces)
        #   10 required_spaces, 2 column = 5 rows (5 x 2 = 10 spaces)
        #   11 required_spaces, 3 column = 4 rows (4 x 3 = 12 spaces)
        rows = int(math.ceil(required_spaces / float(columns)))

        table = gtk.Table(rows, columns * self.COLUMNS_PER_FIELD, False)
        table.props.row_spacing = 6
        table.props.column_spacing = 6

        focus_widgets = []
        used_spaces = set()
        i, j = 0, 0

        # FIXME: This for is more complex than it should. Refactor it in the future
        for field, field_name in fields:
            if field.colspan > columns:
                raise ValueError(
                    "colspan cannot be greater then the number of columns")

            form.build_field(field, field_name)

            # Find a place for the widget. This will search each row of each
            # column ,starting at the first row (j == 0) until the last one.
            # When the first column is completely filled, it will go to the
            # next column and so on.
            while (i, j) in used_spaces:
                j += 1
                if j >= rows:
                    j = 0
                    i += 1

            # Mark i, j as used, even the spaces used by its colspan
            for k in range(i, i + field.colspan):
                used_spaces.add((k, j))

            x = i * self.COLUMNS_PER_FIELD
            y = j

            # Attach the field label
            if field.label_widget:
                table.attach(field.label_widget,
                             x, x + 1, y, y + 1,
                             gtk.FILL, 0, 0, 0)

            x += 1
            if field.colspan > 1:
                extra_x = (field.colspan - 1) * (self.COLUMNS_PER_FIELD + 1)
            else:
                extra_x = 1

            # Attach the field widget
            table.attach(field.get_attachable_widget(),
                         x, x + extra_x, y, y + 1,
                         gtk.EXPAND | gtk.FILL, 0, 0, 0)

            # Build and attach the extra buttons
            hbox = gtk.HBox(spacing=0)
            for button in [field.add_button, field.edit_button, field.delete_button]:
                if not button:
                    continue
                hbox.pack_start(button, expand=False, fill=False)

            x += extra_x
            hbox.show_all()
            table.attach(hbox,
                         x, x + 1, y, y + 1,
                         0, 0, 0, 0)

            focus_widgets.append(field.widget)

        table.set_focus_chain(focus_widgets)
        self.widget = table


class BasicForm(SlaveDelegate):
    """
    I create fields and add the widget representing them
    to another view, this is suitable for forms that can replace
    interface created in glade. This should be used together with
    a kiwi :class:`View`. I also create a proxy for the view if there
    are any widgets that has the proxy property enabled.
    """
    gsignal('button-clicked', Field, str)

    def __init__(self, view):
        """
        :param view: a view to store the created widgets in
        """
        self._fields = {}
        if not view:
            raise TypeError(
                "Form %r requires a view, not %r" % (
                    self.__class__.__name__, view, ))
        self.proxy = None
        self.main_view = view
        # Just a simple GtkBin
        self.toplevel = gtk.Alignment(xscale=1)
        SlaveDelegate.__init__(self)

    def __repr__(self):
        return '<%s of %s>' % (self.__class__.__name__,
                               self.main_view.__class__.__name__)

    # Public API

    def build(self, namespace):
        if not namespace:
            raise TypeError(
                "Form %r requires at least one field" % (self, ))
        fields = []
        for field_name, field in namespace.items():
            if isinstance(field, Field):
                fields.append((field.sort_key, field, field_name))

        fields.sort()
        # Remove sort key
        fields = [field[1:] for field in fields]

        layout = FormTableLayout(self, fields, self.main_view.form_columns)
        self.toplevel.add(layout.widget)
        layout.widget.show()

    def add_proxy(self):
        """Add proxy for this form

        Make sure to call this after the callbacks for self.main_view are
        connected
        """
        if not self._fields:
            return

        proxy_fields = []
        for field_name, field in self._fields.items():
            if field.proxy:
                proxy_fields.append(field_name)
        self.proxy = self.main_view.add_proxy(
            self.main_view.model, proxy_fields)

    def build_field(self, field, model_attribute):
        field.attach_form(self, model_attribute)
        setattr(self.main_view, model_attribute, field.widget)
        if field.label_widget:
            setattr(self.main_view, field.label_attribute, field.label_widget)
        if field.has_add_button:
            setattr(self.main_view,
                    field.model_attribute + '_add_button', field.add_button)
        if field.has_edit_button:
            setattr(self.main_view,
                    field.model_attribute + '_edit_button', field.edit_button)
        if field.has_delete_button:
            setattr(self.main_view,
                    field.model_attribute + '_delete_button', field.delete_button)
        self._fields[model_attribute] = field

    def populate(self, *args):
        for field_name, field in self._fields.items():
            value = getattr(self.main_view.model, field_name, None)
            field.populate(value, *args)

    def button_clicked(self, field, button_type):
        self.emit('button-clicked', field, button_type)
