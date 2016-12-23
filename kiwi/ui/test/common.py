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

from gi.repository import GObject, Gtk, Gdk

from kiwi.utils import gsignal


class WidgetIntrospecter(GObject.GObject):
    gsignal('window-added', object, str, object)
    gsignal('window-removed', object, str)

    def __init__(self):
        GObject.GObject.__init__(self)
        self._objects = {}
        self._id_to_obj = {}  # GdkWindow -> GtkWindow
        self._windows = {}  # toplevels ?

    def _event_handler(self, event):
        # Separate method so we can use return inside
        self._check_event(event)
        Gtk.main_do_event(event)

    def _check_event(self, event):
        window = event.get_window()
        if not window:
            return

        event_type = event.type
        window_type = window.get_window_type()
        try:
            widget = window.get_user_data()
        except ValueError:
            widget = self._id_to_obj.get(window)

        if not isinstance(widget, Gtk.Window):
            return
        widget_name = widget.get_name()

        if event_type == Gdk.MAP:
            if window_type != Gdk.WINDOW_TOPLEVEL:
                # For non toplevels we only care about those which has a menu
                # as the child
                child = widget.get_child()
                if not child or not isinstance(child, Gtk.Menu):
                    return

                # Hack to get all the children of a popup menu in
                # the same namespace as the window they were launched in.
                parent_menu = child._parent_menu
                if parent_menu:
                    main = parent_menu.get_toplevel()
                    widget_name = main.get_name()
            else:
                self._window_added(widget, widget_name)
                self._id_to_obj[window] = widget
        elif (event_type == Gdk.DELETE or
              (event_type == Gdk.WINDOW_STATE and
               event.new_window_state == Gdk.WindowState.WITHDRAWN)):
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
        if not Gdk.event_handler_set:
            raise NotImplementedError
        Gdk.event_handler_set(self._event_handler)

    def parse_one(self, toplevel, gobj):
        if not isinstance(gobj, GObject.GObject):
            raise TypeError

        gtype = gobj
        while True:
            name = GObject.type_name(gtype)
            func = getattr(self, name, None)
            if func:
                if func(toplevel, gobj):
                    break
            if gtype == GObject.GObject.__gtype__:
                break

            gtype = GObject.type_parent(gtype)

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
        name = Gtk.Buildable.get_name(widget)
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
            submenu._parent_menu = item
            for child_item in submenu.get_children():
                child_item._parent_menu = item
            self.parse_one(toplevel, submenu)

    def GtkToolButton(self, toplevel, item):
        item.get_child().set_name(item.get_name())

GObject.type_register(WidgetIntrospecter)
