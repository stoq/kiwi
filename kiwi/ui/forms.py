# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
import gettext

import gobject
import gtk

from kiwi.currency import currency
from kiwi.interfaces import IProxyWidget
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.colorbutton import ProxyColorButton
from kiwi.ui.widgets.combo import ProxyComboEntry
from kiwi.ui.widgets.combobox import ProxyComboBox
from kiwi.ui.widgets.entry import ProxyEntry, ProxyDateEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.utils import gsignal

_ = lambda m: gettext.dgettext('kiwi', m)


class Field(gobject.GObject):
    """
    Properties
    ==========
      - B{data_type}: string
        - Used by proxy_widgets
      - B{mandatory}: bool I{False}
        - Used by proxy_widgets
      - B{label}: string I{None}
        - Text of the label that will be next to the field,
          Can be None for not displaying any label at all
      - B{label_attribute}: string I{None}
        - Name of the label widget inside the view, None
          means it should be model_attribute + '_lbl'
      - B{has_add_button}: bool I{False}
        - If we should add an add button next to the widget
      - B{has_edit_button}: bool I{False}
        - If we should add an edit button next to the widget
      - B{proxy}: bool I{False}
        - If this field should be added to a proxy
    """

    # This is used to sort class variables in creation order
    # which is essentially the same thing as the order in the
    # source file, idea borrowed from Django
    global_sort_key = 0

    data_type = gobject.property(type=object)
    mandatory = gobject.property(type=bool, default=False)
    label = gobject.property(type=str)
    label_attribute = gobject.property(type=str)
    has_add_button = gobject.property(type=bool, default=False)
    has_edit_button = gobject.property(type=bool, default=False)
    proxy = gobject.property(type=bool, default=False)

    # This can be used by subclasses to override the default
    # values for properties
    default_overrides = {}

    def __init__(self, label='', **kwargs):
        self.model_attribute = None

        # Widgets
        self.label_widget = None
        self.widget = None
        self.add_button = None
        self.edit_button = None

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
        self.attach()
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

    # Overridables

    def build_label(self):
        label_widget = ProxyLabel()
        label_widget.set_markup(self.label + ':')
        label_widget.set_alignment(1.0, 0.5)
        return label_widget

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

    def content_changed(self):
        pass

gobject.type_register(Field)


class TextField(Field):
    """
    I am a text field with one line, editable by the user
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
        return widget

gobject.type_register(TextField)


class ChoiceField(Field):
    """
    I am a field representing a choice, normally a ComboBox
    """
    values = gobject.property(type=object)
    use_entry = gobject.property(type=bool, default=False)
    widget_data_type = object

    def build_widget(self):
        if self.use_entry:
            combo = ProxyComboEntry()
        else:
            combo = ProxyComboBox()
        self.fill()
        return combo

    def fill(self):
        if self.values:
            self.widget.prefill(self.values)


class PriceField(Field):
    """
    I am a field representing a price, contain a currency symbol, right-aligned etc.
    """
    widget_data_type = currency

    def build_widget(self):
        entry = ProxyEntry()
        return entry


class DateField(Field):
    """
    I am a field representing a date where the user can chose
    a date from a calendar.
    """
    widget_data_type = datetime.date

    def build_widget(self):
        dateentry = ProxyDateEntry()
        return dateentry


class ColorField(Field):
    """
    I am a field representing a color.
    """
    widget_data_type = str

    def build_widget(self):
        button = ProxyColorButton()
        return button


class FormLayout(object):
    #
    # A Layout is a class that decides how the widgets
    # should be created and put on screen, it needs to:
    # * call form.build_field(field, field_name) for all fields
    #   that are passed into the constructor
    # * pack the following widgets:
    #   * field.label_widget
    #   * field.widget
    #   * field.add_button (can be None)
    #   * field.edit_button (can be None)
    # * setup focus
    # * save the toplevel container as self.widget
    #
    def __init__(self, form, fields):
        self.form = form
        self.fields = fields


class FormTableLayout(FormLayout):
    """Most common layout, a table with four columns:

    +-------+-------+---+----+
    | Value:|Widget |Add|Edit|
    +-------+-------+---+----+
    |  Name:|Widget |Add|Edit|
    +-------+-------+---+----+
    | ....  |...... |...|....|

    Each new field is added as another vertical line.
    """
    def __init__(self, form, fields):
        FormLayout.__init__(self, form, fields)
        table = gtk.Table(len(fields), 4, False)
        table.props.row_spacing = 6

        focus_widgets = []
        for i, (field, field_name) in enumerate(fields):
            form.build_field(field, field_name)
            table.attach(field.label_widget, 0, 1, i, i + 1,
                         gtk.FILL,
                         gtk.EXPAND | gtk.FILL, 0, 0)
            table.attach(field.widget, 1, 2, i, i + 1,
                         gtk.EXPAND | gtk.FILL,
                         gtk.EXPAND | gtk.FILL, 6, 0)
            if field.add_button:
                table.attach(field.add_button, 2, 3, i, i + 1,
                             gtk.SHRINK,
                             gtk.EXPAND | gtk.FILL, 0, 0)
            if field.edit_button:
                table.attach(field.edit_button, 3, 4, i, i + 1,
                             gtk.SHRINK,
                             gtk.EXPAND | gtk.FILL, 0, 0)
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

        layout = FormTableLayout(self, fields)
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
        setattr(self.main_view, field.label_attribute, field.label_widget)
        self._fields[model_attribute] = field

    def populate(self, *args):
        for field_name, field in self._fields.items():
            value = getattr(self.main_view.model, field_name, None)
            field.populate(value, *args)

    def button_clicked(self, field, button_type):
        self.emit('button-clicked', field, button_type)
