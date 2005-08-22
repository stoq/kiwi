#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
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

import gettext
import os
from datetime import date

import gtk
from gazpacho.editor import PropertyCustomEditor
from gazpacho.loader.loader import ObjectBuilder
from gazpacho.loader.custom import Adapter, PythonWidgetAdapter, \
     adapter_registry
from gazpacho.properties import prop_registry, CustomProperty, StringType

from kiwi import _warn
from kiwi.environ import environ
from kiwi.ui.widgets.checkbutton import CheckButton
from kiwi.ui.widgets.combobox import ComboBox, ComboBoxEntry
from kiwi.ui.widgets.entry import Entry
from kiwi.ui.widgets.label import Label
from kiwi.ui.widgets.list import Column, List
from kiwi.ui.widgets.radiobutton import RadioButton
from kiwi.ui.widgets.spinbutton import SpinButton
from kiwi.ui.widgets.textview import TextView

_ = gettext.gettext

class Builder(ObjectBuilder):
    def find_resource(self, filename):
        return environ.find_resource("pixmap", filename)

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
        
        self._view = view
        self._gladefile = environ.find_resource("glade", filename + ".glade")
        self._widgets =  (widgets or view.widgets or [])[:]
        self.gladename = gladename or filename
        self._tree = Builder(self._gladefile, domain=domain)

        self._attach_widgets()
        
    def _attach_widgets(self):
        # Attach widgets in the widgetlist to the view specified, so
        # widgets = [label1, button1] -> view.label1, view.button1
        for w in self._widgets:
            widget = self._tree.get_widget(w)
            if widget is not None:
                setattr(self._view, w, widget)
            else:
                _warn("Widget %s was not found in glade widget tree." % w)
        
    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        widget = self._tree.get_widget(name)
        if widget is None:
            raise AttributeError(
                  "Widget %s not found in view %s" % (name, self._view))
        return widget

    def get_widgets(self):
        return self._tree.get_widgets()

    def signal_autoconnect(self, dic):
        self._tree.signal_autoconnect(dic)        

class DataTypeAdaptor(PropertyCustomEditor):
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

    def get_data_types(self):
        raise NotImplementedError
    
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


class SpinBtnDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(SpinBtnDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()
        
    def get_data_types(self):
        return [(_('Integer'), int),
                (_('Float'), float)]

    def get_editor_widget(self):
        return self._input


class EntryDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(EntryDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Integer'), int),
                (_('Float'), float),
                (_('Date'), date),
                (_('String'), str)]

    def get_editor_widget(self):
        return self._input


class TextViewDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(TextViewDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Integer'), int),
                (_('Float'), float),
                (_('Date'), date),
                (_('String'), str)]

    def get_editor_widget(self):
        return self._input


class RadioBtnDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(RadioBtnDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Boolean'), bool)]

    def get_editor_widget(self):
        return self._input


class CheckBtnDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(CheckBtnDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Boolean'), bool)]

    def get_editor_widget(self):
        return self._input


class ComboBoxDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(ComboBoxDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Boolean'), bool),
                (_('String'), str),
                (_('Integer'), int),
                (_('Float'), float),
                (_('Object'), object)]

    def get_editor_widget(self):
        return self._input


class ComboBoxEntryDataTypeAdaptor(DataTypeAdaptor):
    def __init__(self):
        super(ComboBoxEntryDataTypeAdaptor, self).__init__()
        self._input = self.create_editor()

    def get_data_types(self):
        return [(_('Boolean'), bool),
                (_('String'), str),
                (_('Integer'), int),
                (_('Float'), float),
                (_('Object'), object)]

    def get_editor_widget(self):
        return self._input


class DataTypeProperty(CustomProperty, StringType):
    translatable = False
    def save(self):
        value = self.get()
        return value.__name__

class ModelProperty(CustomProperty):
    translatable = False
    
class CheckButtonAdapter(PythonWidgetAdapter):
    object_type = CheckButton
adapter_registry.register_adapter(CheckButtonAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+checkbutton+CheckButton::data-type', DataTypeProperty,
    editor=CheckBtnDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+checkbutton+CheckButton::model-attribute', ModelProperty)
    
class ComboBoxAdapter(PythonWidgetAdapter):
    object_type = ComboBox
adapter_registry.register_adapter(ComboBoxAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+combobox+ComboBox::data-type', DataTypeProperty,
    editor=ComboBoxDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+combobox+ComboBox::model-attribute', ModelProperty)
    
class ComboBoxEntryAdapter(PythonWidgetAdapter):
    object_type = ComboBoxEntry
adapter_registry.register_adapter(ComboBoxEntryAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+combobox+ComboBoxEntry::data-type', DataTypeProperty,
    editor=ComboBoxEntryDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+combobox+ComboBoxEntry::model-attribute', ModelProperty)
    
class EntryAdapter(PythonWidgetAdapter):
    object_type = Entry
adapter_registry.register_adapter(EntryAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+entry+Entry::data-type', DataTypeProperty,
    editor=EntryDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+entry+Entry::model-attribute', ModelProperty)
    
class LabelAdapter(PythonWidgetAdapter):
    object_type = Label
adapter_registry.register_adapter(LabelAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+label+Label::data-type', DataTypeProperty)
prop_registry.override_simple(
    'kiwi+ui+widgets+label+Label::model-attribute', ModelProperty)

class ColumnAdapter(Adapter):
    object_type = Column
    def construct(self, name, gtype, properties):
        return Column(name)
adapter_registry.register_adapter(ColumnAdapter)
    
class ListAdapter(PythonWidgetAdapter):
    object_type = List
adapter_registry.register_adapter(ListAdapter)
    
class RadioButtonAdapter(PythonWidgetAdapter):
    object_type = RadioButton
adapter_registry.register_adapter(RadioButtonAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+radiobutton+RadioButton::data-type', DataTypeProperty,
    editor=RadioBtnDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+radiobutton+RadioButton::model-attribute', ModelProperty)
    
class SpinButtonAdapter(PythonWidgetAdapter):
    object_type = SpinButton
adapter_registry.register_adapter(SpinButtonAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+spinbutton+SpinButton::data-type', DataTypeProperty,
    editor=SpinBtnDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+spinbutton+SpinButton::model-attribute', ModelProperty)

class TextViewAdapter(PythonWidgetAdapter):
    object_type = TextView
adapter_registry.register_adapter(TextViewAdapter)
prop_registry.override_simple(
    'kiwi+ui+widgets+textview+TextView::data-type', DataTypeProperty,
    editor=TextViewDataTypeAdaptor)
prop_registry.override_simple(
    'kiwi+ui+widgets+textview+TextView::model-attribute', ModelProperty)

    


    
