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
#            Gustavo Rahal <gustavo@async.com.br>
#

"""Defines an enhanced version of GtkEntry"""

import time

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.interfaces import implementsIProxy, implementsIMandatoryProxy
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import gproperty, gsignal

class Entry(gtk.Entry, WidgetMixinSupportValidation):
    """The Kiwi Entry widget has many special features that extend the basic
    gtk entry.
    
    First of all, as every Kiwi Widget, it implements the Proxy protocol.
    As the users types the entry can interact with the application model
    automatically. 
    Kiwi Entry also implements interesting UI additions. If the input data
    does not match the data type of the entry the background nicely fades
    to a light red color. As the background changes an information icon
    appears. When the user passes the mouse over the information icon a
    tooltip is displayed informing the user how to correctly fill the
    entry. When dealing with date and float data-type the information on
    how to fill these entries is displayed according to the current locale.
    """
    implementsIProxy()
    implementsIMandatoryProxy()

    gsignal('changed', 'override')
    # mandatory widgets need to have this signal connected
    gsignal('expose-event', 'override')
    
    gproperty("completion", bool, False, 
              "Completion", gobject.PARAM_READWRITE)

    def __init__(self):
        gtk.Entry.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        self._completion = False
        
        if gtk.pygtk_version < (2,6):
            self.chain_expose = self.chain
        else:
            self.chain_expose = lambda e: gtk.Entry.do_expose_event(self, e)
        
    def do_changed(self):
        """Called when the content of the entry changes.

        Sets an internal variable that stores the last time the user
        changed the entry
        """        
        self._last_change_time = time.time()
        self.chain()
        self.emit('content-changed')

    def prop_get_completion(self):
        return self._completion
    
    def prop_set_completion(self, value):
        self._completion = value

        if not self.get_completion():
            self.enable_completion()

    def enable_completion(self):
        completion = gtk.EntryCompletion()
        completion.set_model(gtk.ListStore(str))
        completion.set_text_column(0)
        completion.set_match_func(self._completion_match_func)
        completion.connect("match-selected", self._on_completion__match_selected)
        self.set_completion(completion)
        return completion
    
    def set_completion_strings(self, strings):
        # Check so we have completion enabled, not this does not
        # depend on the property, the user can manually override it,
        # as long as there is a completion object set
        completion = self.get_completion()
        if not completion:
            completion = self.enable_completion()
            
        model = completion.get_model()
        model.clear()
        for s in strings:
            model.append([s])
            
    def _completion_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return
        
        return model[iter][0].startswith(key)

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        self.set_text(model[iter][0])
        self.set_position(-1)
    
    def read(self):
        """Called after each character is typed. If the input is wrong start 
        complaining
        """
        return self.get_text()

    def update(self, data):
        WidgetMixinSupportValidation.update(self, data)

        if data is ValueUnset or data is None:
            self.set_text("")
            self.draw_mandatory_icon_if_needed()
        else:
            self.set_text(self.type2str(data))

    def set_text(self, text):
        gtk.Entry.set_text(self, text)
        self.emit('content-changed')
        
    def do_expose_event(self, event):
        """Expose-event signal are triggered when a redraw of the widget
        needs to be done.
        
        Draws information and mandatory icons when necessary
        """
        result = self.chain_expose(event)
        
        # this attribute stores the info on where to draw icons and paint
        # the background
        # it's been defined here because it's when we have gdk window available
        self._draw_icon(self.window)
        
        return result    
    
gobject.type_register(Entry)
    
