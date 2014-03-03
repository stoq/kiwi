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
Common routines used by other parts of the ui test framework.
"""

import gobject
import gtk
from gtk import gdk
from gtk.gdk import event_handler_set

from kiwi.utils import gsignal


class WidgetIntrospecter(gobject.GObject):
    gsignal('window-added', object, str, object)
    gsignal('window-removed', object, str)

    def __init__(self):
        gobject.GObject.__init__(self)
        self._objects = {}
        self._id_to_obj = {}  # GdkWindow -> GtkWindow
        self._windows = {}  # toplevels ?

    def _event_handler(self, event):
        # Separate method so we can use return inside
        self._check_event(event)
        gtk.main_do_event(event)

    def _check_event(self, event):
        if not event.window:
            return

        window = event.window
        event_type = event.type
        window_type = window.get_window_type()
        try:
            widget = window.get_user_data()
        except ValueError:
            widget = self._id_to_obj.get(window)

        if not isinstance(widget, gtk.Window):
            return
        widget_name = widget.get_name()

        if event_type == gdk.MAP:
            if window_type != gdk.WINDOW_TOPLEVEL:
                # For non toplevels we only care about those which has a menu
                # as the child
                child = widget.child
                if not child or not isinstance(child, gtk.Menu):
                    return

                # Hack to get all the children of a popup menu in
                # the same namespace as the window they were launched in.
                parent_menu = child.get_data('parent-menu')
                if parent_menu:
                    main = parent_menu.get_toplevel()
                    widget_name = main.get_name()
            else:
                self._window_added(widget, widget_name)
                self._id_to_obj[window] = widget
        elif (event_type == gdk.DELETE or
              (event_type == gdk.WINDOW_STATE and
               event.new_window_state == gdk.WINDOW_STATE_WITHDRAWN)):
            self._window_removed(widget, widget_name)

    def _window_added(self, window, name):
        if name in self._windows:
            return
        self._windows[name] = window

        # Toplevel
        self.parse_one(window, window)
        ns = self._objects[name]
        self.emit('window-added', window, name, ns)

    def _window_removed(self, window, name):
        if not name in self._windows:
            # Error?
            return

        del self._windows[name]
        self.emit('window-removed', window, name)

    def _add_widget(self, toplevel, widget, name):
        toplevel_widgets = self._objects.setdefault(toplevel.get_name(), {})
        if name in toplevel_widgets:
            return

        toplevel_widgets[name] = widget

        # Listen to when the widget is removed from the interface, eg when
        # ::parent changes to None. At that time remove the widget and all
        # the children from the namespace.

        def on_widget__notify_parent(widget, pspec, name, widgets,
                                     signal_container):
            # Only take action when the widget is removed from a parent
            if widget.get_parent() is not None:
                return

            for child_name, child in widgets.items():
                if child.is_ancestor(widget):
                    del widgets[child_name]
            widget.disconnect(signal_container.pop())

        signal_container = []
        sig_id = widget.connect('notify::parent', on_widget__notify_parent,
                                name, toplevel_widgets, signal_container)
        signal_container.append(sig_id)

    # Public API

    def register_event_handler(self):
        if not event_handler_set:
            raise NotImplementedError
        event_handler_set(self._event_handler)

    def parse_one(self, toplevel, gobj):
        if not isinstance(gobj, gobject.GObject):
            raise TypeError

        gtype = gobj
        while True:
            name = gobject.type_name(gtype)
            func = getattr(self, name, None)
            if func:
                if func(toplevel, gobj):
                    break
            if gtype == gobject.GObject.__gtype__:
                break

            gtype = gobject.type_parent(gtype)

    #
    # Special widget handling
    #

    def ignore(self, toplevel, gobj):
        pass

    GtkSeparatorMenuItem = GtkTearoffMenuItem = ignore

    def GtkWidget(self, toplevel, widget):
        """
        Called when a GtkWidget is about to be traversed
        """
        # Workaround to support gtkbuilder and gazpacho
        name = gtk.Buildable.get_name(widget)
        if not name:
            name = widget.get_name()
        self._add_widget(toplevel, widget, name)

    def GtkContainer(self, toplevel, container):
        """
        Called when a GtkContainer is about to be traversed

        Parsers all the children and listens for new children, which
        may be added at a later point.
        """
        for child in container.get_children():
            self.parse_one(toplevel, child)

        def _on_container_add(container, widget):
            self.parse_one(toplevel, widget)
        container.connect('add', _on_container_add)

    def GtkDialog(self, toplevel, dialog):
        """
        Called when a GtkDialog is about to be traversed

        Just parses the widgets embedded in the dialogs.
        """
        self.parse_one(toplevel, dialog.action_area)
        self.parse_one(toplevel, dialog.vbox)

    def GtkMenuItem(self, toplevel, item):
        """
        Called when a GtkMenuItem is about to be traversed

        It does some magic to tie a stronger connection between toplevel
        menuitems and submenus, which later will be used.
        """
        submenu = item.get_submenu()
        if submenu:
            submenu.set_data('parent-menu', item)
            for child_item in submenu.get_children():
                child_item.set_data('parent-menu', item)
            self.parse_one(toplevel, submenu)

    def GtkToolButton(self, toplevel, item):
        item.child.set_name(item.get_name())

gobject.type_register(WidgetIntrospecter)
