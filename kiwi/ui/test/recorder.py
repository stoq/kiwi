#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005,2006 Async Open Source
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
User interface event recorder and serializer.

This module provides an interface for creating, listening to
and saving events.
It uses the gobject introspection base class
L{kiwi.ui.test.common.WidgetIntrospecter} to gather widgets, windows and
other objects.

The user interfaces are saved in a format so they can easily be played
back by simply executing the script through a standard python interpreter.
"""

import atexit
import sys
import time

from gtk import gdk
import gtk

from kiwi.log import Logger
from kiwi.ui.test.common import WidgetIntrospecter
from kiwi.ui.objectlist import ObjectList

try:
    from gobject import add_emission_hook
    add_emission_hook # pyflakes
except ImportError:
    try:
        from kiwi._kiwi import add_emission_hook
        add_emission_hook # pyflakes
    except ImportError:
        add_emission_hook = None

_events = []

log = Logger('recorder')

def register_event_type(event_type):
    """
    Add an event type to a list of event types.

    @param event_type: a L{Event} subclass
    """
    if event_type in _events:
        raise AssertionError("event %s already registered" % event_type)
    _events.append(event_type)

def get_event_types():
    """
    Returns the collection of event types.
    @returns: the event types.
    """
    return _events

class SkipEvent(Exception):
    pass

class Event(object):
    """
    Event is a base class for all events.
    An event represent a user change of an interactive widget.
    @cvar object_type: subclass for type, L{Recorder} uses this to
      automatically attach events to objects when they appear
    """
    object_type = None
    def __init__(self, object, name=None):
        """
        Create a new Event object.
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
    L{Recorder} uses this to automatically attach itself to a signal
    at which point this object will be instantiated.

    @cvar signal_name: signal to listen to
    """
    signal_name = None
    def __init__(self, object, name, args):
        """
        Create a new SignalEvent object.
        @param object:
        @param name:
        @param args:
        """
        Event.__init__(self, object, name)
        self.args = args

    def connect(cls, object, signal_name, cb):
        """
        Calls connect on I{object} for signal I{signal_name}.

        @param object: object to connect on
        @param signal_name: signal name to listen to
        @param cb: callback
        """
        object.connect(signal_name, cb, cls, object)
    connect = classmethod(connect)

#
# Special Events
#

class WindowDeleteEvent(Event):
    """
    This event represents a user click on the close button in the
    window manager.
    """

#
# Signal Events
#

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

class ToolButtonReleaseEvent(SignalEvent):
    """
    This event represents a click on a normal toolbar button
    Hackish, see L{ImageMenuItemButtonReleaseEvent} for more details.
    """
    signal_name = 'button-release-event'
    object_type = gtk.Button

    def serialize(self):
        return '%s.activate()' % self.name
register_event_type(ToolButtonReleaseEvent)

class EntrySetTextEvent(SignalEvent):
    """
    This event represents a content modification of a GtkEntry.
    When the user deletes, clears, adds, modifies the text this
    event will be created.
    """
    signal_name = 'notify::text'
    object_type = gtk.Entry

    def __init__(self, object, name, args):
        SignalEvent.__init__(self, object, name, args)
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
class ObjectListSelectionChanged(SignalEvent):
    """
    This event represents a selection change on a
    L{kiwi.ui.objectlist.ObjectList},
    eg when the user selects or unselects a row.
    It is actually tied to the signal changed on GtkTreeSelection object.
    """
    object_type = ObjectList
    signal_name = 'changed'
    def __init__(self, objectlist, name, args):
        self._objectlist = objectlist
        SignalEvent.__init__(self, objectlist, name=objectlist.get_name(),
                             args=args)
        self.rows = self._get_rows()

    def _get_rows(self):
        selection = self._objectlist.get_treeview().get_selection()

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
        return self._objectlist.get_toplevel()

    def serialize(self):
        return '%s.select_paths(%s)' % (self.name, self.rows)
register_event_type(ObjectListSelectionChanged)

class ObjectListDoubleClick(SignalEvent):
    """
    This event represents a double click on a row in objectlist
    """
    signal_name = 'button-press-event'
    object_type = ObjectList

    def __init__(self, objectlist, name, args):
        event, = args
        if event.type != gdk._2BUTTON_PRESS:
            raise SkipEvent

        SignalEvent.__init__(self, objectlist, name, args)
        self.row = objectlist.get_selected_row_number()

    def connect(cls, orig, signal_name, cb):
        object = orig.get_treeview()
        object.connect(signal_name, cb, cls, orig)
    connect = classmethod(connect)

    def serialize(self):
        return '%s.double_click(%s)' % (self.name, self.row)
register_event_type(ObjectListDoubleClick)

# XXX: ComboMixin -> ???

# class KiwiComboBoxChangedEvent(SignalEvent):
#     """
#     This event represents a a selection of an item
#     in a L{kiwi.ui.widgets.combobox.ComboBoxEntry} or
#     L{kiwi.ui.widgets.combobox.ComboBox}.
#     """
#     signal_name = 'changed'
#     object_type = ComboMixin
#     def __init__(self, combo, name, args):
#         SignalEvent.__init__(self, combo, name, args)
#         self.label = combo.get_selected_label()

#     def serialize(self):
#         return '%s.select_item_by_label("%s")' % (self.name, self.label)

# register_event_type(KiwiComboBoxChangedEvent)

class Recorder(WidgetIntrospecter):
    """
    Recorder takes care of attaching events to widgets, when the appear,
    and creates the events when the user is interacting with some widgets.
    When the tracked program is closed the events are serialized into
    a script which can be played back with help of
    L{kiwi.ui.test.player.Player}.
    """

    def __init__(self, filename):
        """
        Create a new Recorder object.
        @param filename: name of the script
        """
        WidgetIntrospecter.__init__(self)
        self.register_event_handler()
        self.connect('window-removed', self.window_removed)

        self._filename = filename
        self._events = []
        self._listened_objects = []
        self._event_types = self._configure_event_types()
        self._args = None

        # This is sort of a hack, but there are no other realiable ways
        # of actually having something executed after the application
        # is finished
        atexit.register(self.save)

        # Register a hook that is called before normal delete-events
        # because if it's connected using a normal callback it will not
        # be called if the application returns True in it's signal handler.
        if add_emission_hook:
            add_emission_hook(gtk.Window, 'delete-event',
                              self._emission_window__delete_event)

    def execute(self, args):
        self._start_timestamp = time.time()
        self._args = args

        # Run the script
        sys.argv = args
        execfile(sys.argv[0], globals(), globals())

    def _emission_window__delete_event(self, window, event, *args):
        self._add_event(WindowDeleteEvent(window))

        # Yes, please call us again
        return True

    def _configure_event_types(self):
        event_types = {}
        for event_type in get_event_types():
            if event_type.object_type is None:
                raise AssertionError
            elist = event_types.setdefault(event_type.object_type, [])
            elist.append(event_type)

        return event_types

    def _add_event(self, event):
        log("Added event %s" % event.serialize())
        self._events.append((event, time.time()))

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
            event_type, orig = args[-2:]
            try:
                self._add_event(event_type(orig, None, args[:-2]))
            except SkipEvent:
                pass
        event_type.connect(object, event_type.signal_name, on_signal)

    def window_removed(self, wi, window, name):
        # It'll already be trapped if we can use an emission hook
        # skip it here to avoid duplicates
        if not add_emission_hook:
            return
        self._add_event(WindowDeleteEvent(window))

    def parse_one(self, toplevel, gobj):
        WidgetIntrospecter.parse_one(self, toplevel, gobj)

        # mark the object as "listened" to ensure we'll always
        # receive unique objects
        if gobj in self._listened_objects:
            return
        self._listened_objects.append(gobj)

        for object_type, event_types in self._event_types.items():
            if not isinstance(gobj, object_type):
                continue

            for event_type in event_types:
                # These 3 hacks should move into the event class itself
                if event_type == MenuItemActivateEvent:
                    if not isinstance(gobj.get_parent(), gtk.MenuBar):
                        continue
                elif event_type == ToolButtonReleaseEvent:
                    if not isinstance(gobj.get_parent(), gtk.ToolButton):
                        continue
                elif event_type == ButtonClickedEvent:
                    if isinstance(gobj.get_parent(), gtk.ToolButton):
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

        if not self._events:
            return

        try:
            fd = open(self._filename, 'w')
        except IOError:
            raise SystemExit("Could not write: %s" % self._filename)
        fd.write("... -*- Mode: doctest -*-\n")
        fd.write("... run: %s\n" % ' '.join(self._args))
        fd.write(">>> from kiwi.ui.test.runner import runner\n")
        fd.write(">>> runner.start()\n")

        windows = {}

        last = self._events[0][1]
        fd.write('>>> runner.sleep(%2.1f)\n' % (last - self._start_timestamp,))

        for event, timestamp in self._events:
            toplevel = event.toplevel_name
            if not toplevel in windows:
                fd.write('>>> %s = runner.waitopen("%s")\n' % (toplevel,
                                                               toplevel))
                windows[toplevel] = True

            if isinstance(event, WindowDeleteEvent):
                fd.write(">>> %s.delete()\n" % (event.name,))
                fd.write(">>> runner.waitclose('%s')\n" % (event.name,))
                if not event.name in windows:
                    # Actually a bug
                    continue
                del windows[event.name]
            else:
                fd.write(">>> %s.%s\n" % (toplevel, event.serialize()))

            delta = timestamp - last
            if delta > 0.05:
                fd.write('>>> runner.sleep(%2.1f)\n' % (delta,))
            last = timestamp

        fd.write('>>> runner.quit()\n')
        fd.close()
