#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
#            Johan Dahlin <jdahlin@async.com.br>
#            Gustavo Rahal <gustavo@async.com.br>
#            Daniel Saran R. da Cunha <daniel@async.com.br>
#            Evandro Vale Miquelito <evandro@async.com.br>
#

"""Defines enhanced versions of GtkComboBox and GtkComboBoxEntry"""

import gobject
import gtk
from gtk import keysyms 

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy, implementsIMandatoryProxy
from kiwi.ui.widgets.comboboxentry import BaseComboBoxEntry
from kiwi.ui.widgets.proxy import WidgetMixin, WidgetMixinSupportValidation
from kiwi.utils import PropertyObject, gproperty

(COL_COMBO_LABEL,
 COL_COMBO_DATA) = range(2)

__pychecker__ = 'no-classattr'

# 1) strings (DONE)
# 2) strings with data attached (DONE)
# 3) searchable strings (partly done)
# 4) searchable strings with data
# 5) editable strings
# 6) strings with autocompletion
#
# Implementation details
# 1,2   ComboxBox
# 3,4,5 ComboxEntry
# 6     AutoCombo
#
# 5 Does not allow data to be attacheds
# 3-6 supports validation

(COMBO_MODE_UNKNOWN,
 COMBO_MODE_STRING,
 COMBO_MODE_DATA) = range(3)
 
class ComboProxyMixin(object):
    """Our combos always have one model with two columns, one for the string
    that is displayed and one for the object it cames from.
    """
    def __init__(self):
        """Call this constructor after the Combo one"""
        model = gtk.ListStore(str, object)
        self.set_model(model)
        self.mode = COMBO_MODE_UNKNOWN

    def set_mode(self, mode):
        if self.mode != COMBO_MODE_UNKNOWN:
            raise AssertionError
        self.mode = mode

    def __nonzero__(self):
        return True
    
    def __len__(self):
        return len(self.get_model())
    
    def prefill(self, itemdata, sort=False):
        """Fills the Combo with listitems corresponding to the itemdata
        provided.
        
        Parameters:
          - itemdata is a list of strings or tuples, each item corresponding
            to a listitem. The simple list format is as follows::

            >>> [ label0, label1, label2 ]
    
            If you require a data item to be specified for each item, use a
            2-item tuple for each element. The format is as follows::

            >>> [ ( label0, data0 ), (label1, data1), ... ]

          - Sort is a boolean that specifies if the list is to be sorted by
            label or not. By default it is not sorted
        """
        if not isinstance(itemdata, (list, tuple)):
            raise TypeError("'data' parameter must be a list or tuple of item "
                            "descriptions, found %s") % type(itemdata)

        if len(itemdata) == 0:
            self.clear()
            return

        if self.mode == COMBO_MODE_UNKNOWN:
            first = itemdata[0]
            if isinstance(first, str):
                self.set_mode(COMBO_MODE_STRING)
            elif isinstance(first, (tuple, list)):
                self.set_mode(COMBO_MODE_DATA)
            else:
                raise TypeError("Could not determine type, items must "
                                "be strings or tuple/list")
                
        mode = self.mode
        model = self.get_model()

        values = {}
        if mode == COMBO_MODE_STRING:
            if sort:
                itemdata.sort()
                
            for item in itemdata:
                if item in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[item] = None
                    
                model.append((item, None))
        elif mode == COMBO_MODE_DATA:
            if sort:
                itemdata.sort(lambda x, y: cmp(x[0], y[0]))
                
            for item in itemdata:
                text, data = item
                if text in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[text] = None
                model.append((text, data))
        else:
            raise TypeError("Incorrect format for itemdata; see "
                            "docstring for more information")

    def append_item(self, label, data=None):
        """ Adds a single item to the Combo. Takes:
        - label: a string with the text to be added
        - data: the data to be associated with that item
        """
        if not isinstance(label, str):
            raise TypeError("label must be string, found %s" % label)

        if self.mode == COMBO_MODE_UNKNOWN:
            if data is not None:
                self.set_mode(COMBO_MODE_DATA)
            else:
                self.set_mode(COMBO_MODE_STRING)

        model = self.get_model()
        if self.mode == COMBO_MODE_STRING:
            if data is not None:
                raise TypeError("data can not be specified in string mode")
            model.append((label, None))
        elif self.mode == COMBO_MODE_DATA:
            if data is None:
                raise TypeError("data must be specified in string mode")
            model.append((label, data))
        else:
            raise AssertionError

    def clear(self):
        """Removes all items from list"""
        model = self.get_model()
        model.clear()

    def select_item_by_position(self, pos):
        self.set_active(pos)

    def select_item_by_label(self, label):
        model = self.get_model()
        for row in model:
            if row[COL_COMBO_LABEL] == label:
                self.set_active_iter(row.iter)
                break
        else:
            raise KeyError("No item correspond to label %s in the combo %s"
                           % (label, self.name))

    def select_item_by_data(self, data):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("select_item_by_data can only be used in data mode")
        
        model = self.get_model()
        for row in model:
            if row[COL_COMBO_DATA] == data:
                self.set_active_iter(row.iter)
                break
        else:
            raise KeyError("No item correspond to data %r in the combo %s" 
                           % (data, self.name))

    def get_model_strings(self):
        return [row[COL_COMBO_LABEL] for row in self.get_model()]

    def get_model_items(self):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("get_model_items can only be used in data mode")
        
        model = self.get_model()
        items = {}
        for row in model:
            items[row[COL_COMBO_LABEL]] = row[COL_COMBO_DATA]
        
        return items

    def get_selected_label(self):
        iter = self.get_active_iter()
        if not iter:
            return
        
        model = self.get_model()
        return model.get_value(iter, COL_COMBO_LABEL)

    def get_selected_data(self):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("get_selected_data can only be used in data mode")

        iter = self.get_active_iter()
        if not iter:
            return
        
        model = self.get_model()
        return model.get_value(iter, COL_COMBO_DATA)
    
class ComboBox(gtk.ComboBox, ComboProxyMixin, WidgetMixin):
    implementsIProxy()
    def __init__(self):
        WidgetMixin.__init__(self)
        gtk.ComboBox.__init__(self)
        ComboProxyMixin.__init__(self)
        self.connect('changed', self._on__changed)
        
        renderer = gtk.CellRendererText()
        self.pack_start(renderer)
        self.add_attribute(renderer, 'text', COL_COMBO_LABEL)
        self.show()

    def _on__changed(self, combo):
        self.emit('content-changed')
 
    def read(self):
        if self.mode == COMBO_MODE_STRING:
            return self.get_selected_label()
        elif self.mode == COMBO_MODE_DATA:
            return self.get_selected_data()
        
        return ValueUnset
    
    def update(self, data):
        # We dont need validation because the user always
        # choose a valid value
        
        if data is ValueUnset or data is None:
            return
        elif self.mode == COMBO_MODE_STRING:
            self.select_item_by_label(data)
        elif self.mode == COMBO_MODE_DATA:
            self.select_item_by_data(data)
        else:
            raise TypeError("unknown ComboBox mode")
        
    def prefill(self, itemdata, sort=False):
        ComboProxyMixin.prefill(self, itemdata, sort)
    
        # we always have something selected, by default the first item
        self.set_active(0)
        self.emit('content-changed')

    def clear(self):
        ComboProxyMixin.clear(self) 
    
gobject.type_register(ComboBox)

class ComboBoxEntry(PropertyObject, BaseComboBoxEntry, ComboProxyMixin,
                    WidgetMixinSupportValidation):
    implementsIProxy()
    implementsIMandatoryProxy()
    
    # it doesn't make sense to connect to this signal
    # because we want to monitor the entry of the combo
    # not the combo box itself.
    
    gproperty("list-writable", bool, True, "List Writable")
    
    def __init__(self, **kwargs):
        # Order is very important here:
        # 1) Create GObject
        BaseComboBoxEntry.__init__(self)
        # 2) mode is set here
        ComboProxyMixin.__init__(self)
        # 3) Properties are now being set, requires 1 & 2
        PropertyObject.__init__(self, **kwargs)
        WidgetMixinSupportValidation.__init__(self, widget=self.entry)
        
        self.set_text_column(COL_COMBO_LABEL)
        # here we connect the expose-event signal directly to the entry
        self.child.connect('changed', self._on_child_entry__changed)
        
        # HACK! we force a queue_draw because when the window is first
        # displayed the icon is not drawn.
        gobject.idle_add(self.queue_draw)

        self.set_events(gtk.gdk.KEY_RELEASE_MASK)
        self.connect("key-release-event", self._on__key_release_event)
    
        self.show()
    
    def prop_set_list_writable(self, writable):
        if self.mode == COMBO_MODE_DATA:
            return
        
        self.entry.set_editable(writable)

    def _update_selection(self, text=None):
        if text is None:
            text = self.entry.get_text()

        self.select_item_by_label(text)
    
    def _add_text_to_combo_list(self):
        text = self.entry.get_text()
        if not text.strip():
            return

        if text in self.get_model_strings():
            return
        
        self.entry.set_text('')
        self.append_item(text)
        self._update_selection(text)
        
    def _on__key_release_event(self, widget, event):
        """Checks for "Enter" key presses and add the entry text to 
        the combo list if the combo list is set as editable.
        """
        if not self.list_writable:
            return

        if event.keyval in (keysyms.KP_Enter,
                            keysyms.Return):
            self._add_text_to_combo_list()

    def _on_child_entry__changed(self, widget):
        """Called when something on the entry changes"""
        if not widget.get_text():
            return

        self.emit('content-changed')

    def set_mode(self, mode):
        # If we're in the transition to go from
        # unknown->label set editable to False
        if (self.mode == COMBO_MODE_UNKNOWN and mode == COMBO_MODE_DATA):
            self.entry.set_editable(False)
            
        ComboProxyMixin.set_mode(self, mode)
        
    def read(self):
        if self.mode == COMBO_MODE_STRING:
            return self.get_selected_label()
        elif self.mode == COMBO_MODE_DATA:
            return self.get_selected_data()
        
        return ValueUnset

    def before_validate(self, data):
        """ComboBoxEntry has a validate default handler that check if the
        text of the entry is an item of the list"""
        
        # XXX: Check so data is in list
        #items = self.get_model_items()
        #if data not in items.keys():
        #    raise ValidationError("Entered value not in list")
        
        return self.read()

    def update(self, data):
        if data is ValueUnset or data is None:
            self.entry.set_text("")
        elif self.mode == COMBO_MODE_STRING:
            self.select_item_by_label(data)
        elif self.mode == COMBO_MODE_DATA:
            self.select_item_by_data(data)
        else:
            raise AssertionError

    def prefill(self, itemdata, sort=False, clear_entry=False):
        ComboProxyMixin.prefill(self, itemdata, sort)
        if clear_entry:
            self.entry.set_text("")

        # setup the autocompletion
        auto = gtk.EntryCompletion()
        auto.set_model(self.get_model())
        auto.set_text_column(COL_COMBO_LABEL)
        self.entry.set_completion(auto)
        
    def clear(self):
        """Removes all items from list and erases entry"""
        ComboProxyMixin.clear(self)
        self.entry.set_text("")

    # IconEntry
    
    def set_pixbuf(self, pixbuf):
        self.entry.set_pixbuf(pixbuf)

    def update_background(self, color):
        self.entry.update_background(color)

    def get_icon_window(self):
        return self.entry.get_icon_window()
