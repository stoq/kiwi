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
# Author(s): Johan Dahlin <jdahlin@async.com.br
#

"""
User interface event listener and serializer.

This module provides an interface for creating, listening to
and saving events.
It uses the gobject introspection base class
L{kiwi.ui.test.common.Base} to gather widgets, windows and other objects.

The user interfaces are saved in a format so they can easily be played
back by simply executing the script through a standard python interpreter.
"""

import atexit

import gtk

from kiwi.ui.test.common import Base
from kiwi.ui.widgets.combobox import ComboProxyMixin
from kiwi.ui.widgets.list import List

_events = []

def register_event_type(event_type):
    """
    Add an event type to a list of event types.
    
    @param event_type: a L{Event} subclass
    """
    if event_type in _events:
        raise AssertionError
    _events.append(event_type)

def get_event_types():
    """
    Returns the collection of event types.
    @returns: the event types.
    """
    return _events

class Event(object):
    """
    Event is a base class for all events.
    An event represent a user change of an interactive widget.
    @cvar object_type: subclass for type, L{Listener} uses this to
      automatically attach events to objects when they appear
    """
    object_type = None
    def __init__(self, object, name=None):
        """
        @param object: a gobject subclass
        @param name: name of the object, if None, the
          method get_name() will be called
        """
        self.object = object
        if name is None:
            name = object.get_name()
        self.name = name
        self.toplevel_name = self.get_toplevel(object).get_name()
        
    # Override in subclass
    def get_toplevel(self, widget):
        """
        This fetches the toplevel widget for a specific object,
        by default it assumes it's a wiget subclass and calls
        get_toplevel() for the widget
        
        Override this in a subclass.
        """
        return widget.get_toplevel()
        
    def serialize(self):
        """
        Serialize the widget, write the code here which is
        used to reproduce the event, for a button which is clicked
        the implementation looks like this:

        >>> def serialize(self):
        >>> ... return '%s.clicked' % self.name

        @returns: string to reproduce event
        Override this in a subclass.
        """
        pass
    
class SignalEvent(Event):
    """
    A SignalEvent is an L{Event} which is tied to a GObject signal,
    L{Listener} uses this to automatically attach itself to a signal
    at which point this object will be instantiated.
    
    @cvar signal_name: signal to listen to
    """
    signal_name = None

    def connect(cls, object, signal_name, cb):
        """
        Calls connect on I{object} for signal I{signal_name}.

        @param object: object to connect on
        @param signal_name: signal name to listen to
        @param cb: callback
        """
        object.connect(signal_name, cb, cls, object)
    connect = classmethod(connect)

class WindowDeleteEvent(SignalEvent):
    """
    This event represents a user click on the close button in the
    window manager.
    """
    
    signal_name = 'delete-event'
    object_type = gtk.Window

    def serialize(self):
        return 'delete_window("%s")' % self.name
    
register_event_type(WindowDeleteEvent)

class MenuItemActivateEvent(SignalEvent):
    """
    This event represents a user click on a menu item.
    It could be a toplevel or a normal entry in a submenu.
    """
    signal_name = 'activate'
    object_type = gtk.MenuItem

    def serialize(self):
        return '%s.activate()' % self.name
register_event_type(MenuItemActivateEvent)

class ImageMenuItemButtonReleaseEvent(SignalEvent):
    """
    This event represents a click on a normal menu entry
    It's sort of a hack to use button-press-event, instea
    of listening to activate, but we'll get the active callback
    after the user specified callbacks are called, at which point
    it is already too late.
    """
    signal_name = 'button-release-event'
    object_type = gtk.ImageMenuItem
    
    def get_toplevel(self, widget):
        parent = widget
        while True:
            widget = parent.get_data('parent-menu')
            if not widget:
                break
            parent = widget
        toplevel = parent.get_toplevel()
        return toplevel
    
    def serialize(self):
        return '%s.activate()' % self.name
register_event_type(ImageMenuItemButtonReleaseEvent)

class EntrySetTextEvent(SignalEvent):
    """
    This event represents a content modification of a GtkEntry.
    When the user deletes, clears, adds, modifies the text this
    event will be created.
    """
    signal_name = 'notify::text'
    object_type = gtk.Entry

    def __init__(self, object):
        SignalEvent.__init__(self, object)
        self.text = self.object.get_text()

    def serialize(self):
        return '%s.set_text("%s")' % (self.name, self.text)
register_event_type(EntrySetTextEvent)

class EntryActivateEvent(SignalEvent):
    """
    This event represents an activate event for a GtkEntry, eg when
    the user presses enter in a GtkEntry.
    """
    
    signal_name = 'activate'
    object_type = gtk.Entry

    def serialize(self):
        return '%s.activate()' % (self.name)
register_event_type(EntryActivateEvent)

# Also works for Toggle, Radio and Check
class ButtonClickedEvent(SignalEvent):
    """
    This event represents a button click.
    Note that this will also work for GtkToggleButton, GtkRadioButton
    and GtkCheckButton.
    """
    signal_name = 'clicked'
    object_type = gtk.Button

    def serialize(self):
        return '%s.clicked()' % self.name
register_event_type(ButtonClickedEvent)
    
# Kiwi widget support
class KiwiListSelectionChanged(SignalEvent):
    """
    This event represents a selection change on a L{kiwi.ui.widgets.list.List},
    eg when the user selects or unselects a row.
    It is actually tied to the signal changed on GtkTreeSelection object.
    """
    object_type = List
    signal_name = 'changed'
    def __init__(self, klist):
        self._klist = klist
        super(SignalEvent, self).__init__(object=klist,
                                          name=klist.get_name())
        self.rows = self._get_rows()
        
    def _get_rows(self):
        selection = self._klist.get_treeview().get_selection()
        
        if selection.get_mode() == gtk.SELECTION_MULTIPLE:
            # get_selected_rows() returns a list of paths
            iters = selection.get_selected_rows()[1]
            if iters:
                return iters
        else:
            # while get_selected returns an iter, yay.
            model, iter = selection.get_selected()
            if iter is not None:
                # so convert it to a path and put it in an empty list
                return [model.get_string_from_iter(iter)]

        return []
                
    def connect(cls, orig, signal_name, cb):
        object = orig.get_treeview().get_selection()
        object.connect(signal_name, cb, cls, orig)
    connect = classmethod(connect)
    
    def get_toplevel(self, widget):
        return self._klist.get_toplevel()
    
    def serialize(self):
        return '%s.select_paths(%s)' % (self.name, self.rows)
register_event_type(KiwiListSelectionChanged)

class KiwiComboBoxChangedEvent(SignalEvent):
    """
    This event represents a a selection of an item
    in a L{kiwi.ui.widgets.combobox.ComboBoxEntry} or
    L{kiwi.ui.widgets.combobox.ComboBox}.
    """
    signal_name = 'changed'
    object_type = ComboProxyMixin
    def __init__(self, combo):
        SignalEvent.__init__(self, combo)
        self.label = combo.get_selected_label()
        
    def serialize(self):
        return '%s.select_item_by_label("%s")' % (self.name, self.label)

register_event_type(KiwiComboBoxChangedEvent)

class Listener(Base):
    """
    Listener takes care of attaching events to widgets, when the appear,
    and creates the events when the user is interacting with some widgets.
    When the tracked program is closed the events are serialized into
    a script which can be played back with help of
    L{kiwi.ui.test.player.Player}.
    """
    
    def __init__(self, filename, args):
        """
        @param filename: name of the script
        @param args: command line used to run the script
        """
        Base.__init__(self)
        self._filename = filename
        self._args = args
        self._events = []
        self._listened_objects = []
        self._event_types = self._configure_event_types()
        
        atexit.register(self.save)

    def _configure_event_types(self):
        event_types = {}
        for event_type in get_event_types():
            if event_type.object_type is None:
                raise AssertionError
            elist = event_types.setdefault(event_type.object_type, [])
            elist.append(event_type)
            
        return event_types
    
    def _add_event(self, event):
        self._events.append(event)

    def _listen_event(self, object, event_type):
        if not issubclass(event_type, SignalEvent):
            raise TypeError("Can only listen to SignalEvents, not %r"
                            % event_type)

        if event_type.signal_name is None:
            raise ValueError("signal_name cannot be None")

        # This is horrible, but there's no good way of passing in
        # more than one variable to the script and we really want to be
        # able to connect it to any kind of signal, regardless of
        # the number of parameters the signal has
        def on_signal(object, *args):
            event_type = args[-2]
            orig = args[-1]
            #print 'Creating event', event_type, object.get_name()
            self._add_event(event_type(orig))
        #print '%s %s->%s' % (object.__class__.__name__,
        #                     object.get_name(), event_type.signal_name)
        event_type.connect(object, event_type.signal_name, on_signal)

    def window_removed(self, window):
        self._add_event(WindowDeleteEvent(window))

    def parse_one(self, toplevel, gobj):
        Base.parse_one(self, toplevel, gobj)

        # mark the object as "listened" to ensure we'll always
        # receive unique objects
        listened = gobj in self._listened_objects
        if listened:
            return
        self._listened_objects.append(gobj)
            
        for object_type, event_types in self._event_types.items():
            if not isinstance(gobj, object_type):
                continue

            for event_type in event_types:
                if event_type == MenuItemActivateEvent:
                    if not isinstance(gobj.get_parent(), gtk.MenuBar):
                        continue
                if issubclass(event_type, SignalEvent):
                    self._listen_event(gobj, event_type)
                    
    def save(self):
        """
        Collect events and serialize them into a script and save
        the script.
        This should be called when the tracked program has
        finished executing.
        """
        
        try:
            fd = open(self._filename, 'w')
        except IOError:
            raise SystemExit("Could not write: %s" % self._filename)
        fd.write("from kiwi.ui.test.player import Player\n"
                 "\n"
                 "player = Player(%s)\n"
                 "app = player.get_app()\n" % repr(self._args))
        
        windows = {}
        
        for event in self._events:
            toplevel = event.toplevel_name
            if not toplevel in windows:
                fd.write('\n'
                         'player.wait_for_window("%s")\n' % toplevel)
                windows[toplevel] = True

            if isinstance(event, WindowDeleteEvent):
                fd.write("player.%s\n\n" % (event.serialize()))
                if not event.name in windows:
                    # Actually a bug
                    continue
                del windows[event.name]
            else:
                fd.write("app.%s.%s\n" % (toplevel,
                                          event.serialize()))

        fd.write('player.finish()\n')
        fd.close()
