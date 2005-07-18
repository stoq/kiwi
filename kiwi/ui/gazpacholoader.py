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

import os

from gazpacho.loader.loader import ObjectBuilder
from gazpacho.loader.custom import Adapter, PythonWidgetAdapter

from kiwi import _warn
from kiwi.environ import find_in_gladepath, image_path_resolver
from kiwi.ui.widgets.checkbutton import CheckButton
from kiwi.ui.widgets.combobox import ComboBox, ComboBoxEntry
from kiwi.ui.widgets.entry import Entry
from kiwi.ui.widgets.label import Label
from kiwi.ui.widgets.list import Column, List
from kiwi.ui.widgets.radiobutton import RadioButton
from kiwi.ui.widgets.spinbutton import SpinButton
from kiwi.ui.widgets.textview import TextView

class Builder(ObjectBuilder):
    find_resource = image_path_resolver

class GazpachoWidgetTree:
    """Example class of GladeAdaptor that uses Gazpacho loader to load the
    glade files
    """
    def __init__(self, view, gladefile, widgets, gladename=None):

        if not gladefile:
            raise ValueError("A gladefile wasn't provided.")
        elif not isinstance(gladefile, basestring):
            raise TypeError(
                  "gladefile should be a string, found %s" % type(gladefile))
        filename = os.path.splitext(os.path.basename(gladefile))[0]
        
        self._view = view
        self._gladefile = find_in_gladepath(filename + ".glade")
        self._widgets =  (widgets or view.widgets or [])[:]
        self.gladename = gladename or filename
        self._tree = Builder(self._gladefile)

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

class CheckButtonAdapter(PythonWidgetAdapter):
    object_type = CheckButton
    
class ComboBoxdapter(PythonWidgetAdapter):
    object_type = ComboBox
    
class ComboBoxEntryAdapter(PythonWidgetAdapter):
    object_type = ComboBoxEntry
    
class EntryAdapter(PythonWidgetAdapter):
    object_type = Entry
    
class LabelAdapter(PythonWidgetAdapter):
    object_type = Label

class ColumnAdapter(Adapter):
    object_type = Column
    def construct(self, name, gtype, properties):
        print name, properties
        obj = Column(name)
        return obj
    
class ListAdapter(PythonWidgetAdapter):
    object_type = List
    
class RadioButtonAdapter(PythonWidgetAdapter):
    object_type = RadioButton
    
class SpinButtonAdapter(PythonWidgetAdapter):
    object_type = SpinButton
    
class TextViewAdapter(PythonWidgetAdapter):
    object_type = TextView

