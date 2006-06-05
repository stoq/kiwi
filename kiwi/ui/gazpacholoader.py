#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
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
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""Gazpacho integration: loader and extensions"""

import datetime
import gettext
import os
import warnings

import gobject
import gtk
from gazpacho.editor import PropertyCustomEditor
from gazpacho.loader.loader import ObjectBuilder
from gazpacho.loader.custom import Adapter, ComboBoxAdapter, \
     PythonWidgetAdapter, adapter_registry
from gazpacho.properties import prop_registry, CustomProperty, StringType
from gazpacho.widgets.base.base import ContainerAdaptor
from gazpacho.widgets.base.box import BoxAdaptor

from kiwi.datatypes import currency, Decimal
from kiwi.environ import environ
from kiwi.log import Logger
from kiwi.python import disabledeprecationcall
from kiwi.ui.hyperlink import HyperLink
from kiwi.ui.objectlist import Column, ObjectList
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox, \
     ProxyComboBoxEntry
from kiwi.ui.widgets.entry import ProxyDateEntry, ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.radiobutton import ProxyRadioButton
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView

# Backwards compatibility + pyflakes
from kiwi.ui.widgets.combobox import ComboBox, ComboBoxEntry
from kiwi.ui.widgets.list import List
HyperLink
_ = lambda m: gettext.dgettext('kiwi', m)

log = Logger('gazpacholoader')

class Builder(ObjectBuilder):
    def find_resource(self, filename):
        return environ.find_resource("pixmaps",  filename)

class GazpachoWidgetTree:
    """Example class of GladeAdaptor that uses Gazpacho loader to load the
    glade files
    """
    def __init__(self, view, gladefile, widgets, gladename=None, domain=None):

        if not gladefile:
            raise ValueError("A gladefile wasn't provided.")
        elif not isinstance(gladefile, basestring):
            raise TypeError(
                  "gladefile should be a string, found %s" % type(gladefile))
        filename = os.path.splitext(os.path.basename(gladefile))[0]
        self._filename = filename + '.glade'
        self._view = view
        self._gladefile = environ.find_resource("glade", self._filename)
        self._widgets =  (widgets or view.widgets or [])[:]
        self.gladename = gladename or filename
        self._showwarning = warnings.showwarning
        warnings.showwarning = self._on_load_warning
        self._tree = Builder(self._gladefile, domain=domain)
        warnings.showwarning = self._showwarning
        if not self._widgets:
            self._widgets = [w.get_data("gazpacho::object-id")
                             for w in self._tree.get_widgets()]
        self._attach_widgets()

    def _on_load_warning(self, warning, category, file, line):
        self._showwarning('while loading glade file: %s' % warning,
                          category, self._filename, '???')

    def _attach_widgets(self):
        # Attach widgets in the widgetlist to the view specified, so
        # widgets = [label1, button1] -> view.label1, view.button1
        for w in self._widgets:
            widget = self._tree.get_widget(w)
            if widget is not None:
                setattr(self._view, w, widget)
            else:
                log.warn("Widget %s was not found in glade widget tree." % w)

    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        name = name.replace('-', '_')
        widget = self._tree.get_widget(name)
        if widget is None:
            raise AttributeError(
                  "Widget %s not found in view %s" % (name, self._view))
        return widget

    def get_widgets(self):
        return self._tree.get_widgets()

    def signal_autoconnect(self, dic):
        self._tree.signal_autoconnect(dic)

    def get_sizegroups(self):
        return self._tree.sizegroups

# Normal widgets
for prop in ('normal-color', 'normal-underline', 'normal-bold',
             'hover-color', 'hover-underline', 'hover-bold',
             'active-color', 'active-underline', 'active-bold'):
    prop_registry.override_simple('HyperLink::%s' % prop, editable=False)

class HyperLinkAdaptor(ContainerAdaptor):
    def fill_empty(self, context, widget):
        pass

    def post_create(self, context, widget, interactive):
        widget.set_text(widget.get_name())

class ComboEntryAdaptor(BoxAdaptor):
    def get_children(self, context, comboentry):
        return []

class DateEntryAdaptor(BoxAdaptor):
    def get_children(self, context, comboentry):
        return []

class KiwiColumnAdapter(Adapter):
    object_type = Column
    def construct(self, name, gtype, properties):
        return Column(name)
adapter_registry.register_adapter(KiwiColumnAdapter)

class ObjectListAdapter(PythonWidgetAdapter):
    object_type = ObjectList
    def construct(self, name, gtype, properties):
        if gtype == List:
            gtype == ObjectList
        return super(ObjectListAdapter, self).construct(name, gtype,
                                                        properties)
adapter_registry.register_adapter(ObjectListAdapter)

# Framework widgets

class DataTypeAdaptor(PropertyCustomEditor):
    def __init__(self):
        super(DataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_editor_widget(self):
        return self._input

    def get_data_types(self):
        """
        Subclasses should override this.
        Expected to return a list of 2 sized tuples with
        name of type and type, to be used in a combo box.
        """
        raise NotImplementedError

    def create_editor(self):
        model = gtk.ListStore(str, object)
        for datatype in self.get_data_types():
            model.append(datatype)
        combo = gtk.ComboBox(model)
        renderer = gtk.CellRendererText()
        combo.pack_start(renderer)
        combo.add_attribute(renderer, 'text', 0)
        combo.set_active(0)
        combo.set_data('connection-id', -1)
        return combo

    def update(self, context, kiwiwidget, proxy):
        combo = self._input
        connection_id = combo.get_data('connection-id')
        if (connection_id != -1):
            combo.disconnect(connection_id)
        model = combo.get_model()
        connection_id = combo.connect('changed', self._editor_edit,
                                      proxy, model)
        combo.set_data('connection-id', connection_id)
        value = kiwiwidget.get_property('data-type')
        for row in model:
            if row[1] == value:
                combo.set_active_iter(row.iter)
                break

    def _editor_edit(self, combo, proxy, model):
        active_iter = combo.get_active_iter()
        proxy.set_value(model[active_iter][1])

class SpinBtnDataType(DataTypeAdaptor):
    def get_data_types(self):
        return [
            (_('Integer'), int),
            (_('Float'), float),
            (_('Decimal'), Decimal),
            (_('Currency'), currency)
            ]

class EntryDataType(DataTypeAdaptor):
    def get_data_types(self):
        return [
            (_('String'), str),
            (_('Unicode'), unicode),
            (_('Integer'), int),
            (_('Float'), float),
            (_('Decimal'), Decimal),
            (_('Currency'), currency),
            (_('Date'), datetime.date),
            (_('Date and Time'), datetime.datetime),
            (_('Time'), datetime.time),
            (_('Object'), object)
            ]

class TextViewDataType(DataTypeAdaptor):
    def get_data_types(self):
        return [
            (_('String'), str),
            (_('Unicode'), unicode),
            (_('Integer'), int),
            (_('Float'), float),
            (_('Decimal'), Decimal),
            (_('Date'), datetime.date),
            ]

class ComboBoxDataType(DataTypeAdaptor):
    def get_data_types(self):
        return [
            (_('String'), str),
            (_('Unicode'), unicode),
            (_('Boolean'), bool),
            (_('Integer'), int),
            (_('Float'), float),
            (_('Decimal'), Decimal),
            (_('Object'), object)
            ]

class LabelDataType(DataTypeAdaptor):
    def get_data_types(self):
        return [
            (_('String'), str),
            (_('Unicode'), unicode),
            (_('Boolean'), bool),
            (_('Integer'), int),
            (_('Float'), float),
            (_('Decimal'), Decimal),
            (_('Date'), datetime.date),
            (_('Date and Time'), datetime.datetime),
            (_('Time'), datetime.time),
            (_('Currency'), currency)
            ]

class DataType(CustomProperty, StringType):
    translatable = False
    def save(self):
        value = self.get()
        if value is not None:
            return value.__name__

class BoolOnlyDataType(CustomProperty, StringType):
    translatable = False
    editable = False
    def save(self):
        return 'bool'

class DateOnlyDataType(CustomProperty, StringType):
    translatable = False
    editable = False
    def save(self):
        return 'date'

class ModelProperty(CustomProperty, StringType):
    translatable = False

class DataValueProperty(CustomProperty, StringType):
    translatable = False

# Register widgets which have data-type and model-attributes
# ComboBox is a special case, it needs to inherit from another
# adapter and need to support two types.
class KiwiComboBoxAdapter(ComboBoxAdapter):
    object_type = ProxyComboBox, ProxyComboBoxEntry
    def construct(self, name, gtype, properties):
        if gtype in (ProxyComboBox.__gtype__,
                     ComboBox.__gtype__):
            object_type = ProxyComboBox
        elif gtype in (ProxyComboBoxEntry.__gtype__,
                       ComboBoxEntry.__gtype__):
            object_type = ProxyComboBoxEntry
        else:
            raise AssertionError("Unknown ComboBox GType: %r" % gtype)

        obj = disabledeprecationcall(object_type)
        obj.set_name(name)
        return obj
adapter_registry.register_adapter(KiwiComboBoxAdapter)

def register_widgets():
    for gobj, editor, data_type in [
        (ProxyEntry, EntryDataType, DataType),
        (ProxyDateEntry, None, DateOnlyDataType),
        (ProxyCheckButton, None, BoolOnlyDataType),
        (ProxyLabel, LabelDataType, DataType),
        (ProxyComboBox, ComboBoxDataType, DataType),
        (ProxyComboBoxEntry, ComboBoxDataType, DataType),
        (ProxyComboEntry, ComboBoxDataType, DataType),
        (ProxySpinButton, SpinBtnDataType, DataType),
        (ProxyRadioButton, None, BoolOnlyDataType),
        (ProxyTextView, TextViewDataType, DataType)
        ]:
        # Property overrides, used in the editor
        type_name = gobject.type_name(gobj)

        data_name = type_name + '::data-type'
        if editor:
            prop_registry.override_simple(data_name, data_type, custom_editor=editor)
        else:
            prop_registry.override_simple(data_name, data_type)

        prop_registry.override_simple(type_name + '::model-attribute',
                                      ModelProperty)

        if issubclass(gobj, ProxyRadioButton):
            prop_registry.override_simple(type_name + '::data-value',
                                          DataValueProperty)
        # Register custom adapters, since gobject.new is broken in 2.6
        # Used by loader, eg in gazpacho and in applications
        # ComboBox is registered above
        if gobj == ProxyComboBox:
            continue

        klass = type('Kiwi%sAdapter', (PythonWidgetAdapter,),
                     dict(object_type=gobj))
        adapter_registry.register_adapter(klass)

if not environ.epydoc:
    register_widgets()
