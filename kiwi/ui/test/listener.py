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

import atexit

import gtk

from kiwi.ui.test.common import Base

_events = []

def register_event_type(event_type):
    if event_type in _events:
        raise AssertionError
    _events.append(event_type)

def get_event_types():
    return _events

class Event:
    object_type = None
    def __init__(self, object):
        self.object = object
        self.name = object.get_name()
        self.toplevel_name = self.get_toplevel(object).get_name()
        
    # Override in subclass
    def get_toplevel(self, widget):
        return widget.get_toplevel()
        
    def serialize(self):
        pass

class SignalEvent(Event):
    signal_name = None

class WindowAddedEvent(Event):
    object_type = gtk.Window

    def serialize(self):
        return 'wait_for_window("%s")' % self.name
register_event_type(WindowAddedEvent)
    
class WindowDeleteEvent(SignalEvent):
    signal_name = 'delete-event'
    object_type = gtk.Window

    def serialize(self):
        return 'delete_window("%s")' % self.name
    
register_event_type(WindowDeleteEvent)

class MenuItemActivateEvent(SignalEvent):
    """
    MenuItemActivatedEvent is created when the user clicks
    on a menu item. It could be a toplevel or a normal entry in
    a submenu.
    """
    signal_name = 'activate'
    object_type = gtk.MenuItem

    def serialize(self):
        return '%s.activate()' % self.name
register_event_type(MenuItemActivateEvent)

class ImageMenuItemButtonReleaseEvent(SignalEvent):
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
    EntrySetTextEvent is created when the content of a GtkEntry changes
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
    signal_name = 'activate'
    object_type = gtk.Entry

    def serialize(self):
        return '%s.activate()' % (self.name)
register_event_type(EntryActivateEvent)

class ButtonClickedEvent(SignalEvent):
    signal_name = 'clicked'
    object_type = gtk.Button

    def serialize(self):
        return '%s.clicked()' % self.name
register_event_type(ButtonClickedEvent)

class Listener(Base):
    def __init__(self, filename, args):
        """
        @param filename:
        @param args:
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
            event_type = args[-1]
            #print 'Creating event', event_type, object.get_name()
            self._add_event(event_type(object))
        #print '%s %s->%s' % (object.__class__.__name__,
        #                     object.get_name(), event_type.signal_name)
        object.connect(event_type.signal_name, on_signal, event_type)

    def window_added(self, window):
        self._add_event(WindowAddedEvent(window))

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
        template = ("from kiwi.ui.test.player import Player\n"
                    "\n"
                    "player = Player(%s)\n"
                    "app = player.get_app()\n")

        fd = file(self._filename, 'w')
        fd.write(template % self._args)
        
        for event in self._events:
            if isinstance(event, (WindowAddedEvent,
                                  WindowDeleteEvent)):
                fd.write("\n"
                         "player.%s\n" % (event.serialize()))
            else:
                fd.write("app.%s.%s\n" % (event.toplevel_name,
                                          event.serialize()))

        fd.write('player.finish()\n')
        fd.close()
