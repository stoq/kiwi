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

"""XXX"""

import sets

import gobject
import gtk

class Base(object):
    def __init__(self):
        self._windows = {}
        self._window_list = self._list_windows()
        gobject.timeout_add(25, self._check_windows)
        self._objects = {}

    # Public API
    
    def parse_one(self, toplevel, gobj):
        """
        @param gobj:
        """
        
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
        
    # Override in subclass
    
    def window_added(self, window):
        """
        This will be called when a window is displayed
        @param window:
        """

    def window_removed(self, window):
        """
        This will be called when a window is destroyed
        @param window: 
        """

    # Private

    def _on_window_name_change(self, window, pspec, old_name):
        # Update datastructures, no need to notify that the dialog
        # was added, we already know about it and all its children
        self._windows[window.get_name()] = self._windows.pop(old_name)
        
    def _list_windows(self):
        # We're only interested in toplevels for now, tooltip windows are
        # popups for example
        rv = []
        for window in gtk.window_list_toplevels():
            if window.type != gtk.WINDOW_TOPLEVEL:
                if not isinstance(window.child, gtk.Menu):
                    continue
                
                # Hack to get all the entries of a popup menu in
                # the same namespace as the window they were launched
                # in.
                parent_menu = window.child.get_data('parent-menu')
                if parent_menu:
                    main = parent_menu.get_toplevel()
                    rv.append((main.get_name(), window))
            else:
                rv.append((window.get_name(), window))
                
        return sets.Set(rv)

    def _check_windows(self):
        new_windows = self._list_windows()
        if self._windows != new_windows:
            for name, window in new_windows.difference(self._window_list):
                # Popup window, eg menu popups needs to be treated
                # specially, only parse the contained widgets, do not
                # add it or listen to name changes, we don't care about them
                if window.type == gtk.WINDOW_POPUP:
                    toplevel = self._windows[name]
                    self.parse_one(toplevel, window)
                else:
                    self.parse_one(window, window)
                    
                    window.connect('notify::name', self._on_window_name_change,
                                   window.get_name())
                    self.window_added(window)
                    self._windows[name] = window
                
            for name, window in self._window_list.difference(new_windows):
                # We don care about popup windows, see above
                if window.type == gtk.WINDOW_POPUP:
                    continue
                
                self.window_removed(window)
                del self._windows[name]
                
            self._window_list = new_windows
        return True

    def ignore(self, toplevel, gobj): pass
    
    GtkSeparatorMenuItem = GtkTearoffMenuItem = ignore

    def GtkWidget(self, toplevel, widget):
        toplevel_widgets = self._objects.setdefault(toplevel.get_name(), {})
        toplevel_widgets[widget.get_name()] = widget

    def GtkContainer(self, toplevel, container):
        for child in container.get_children():
            self.parse_one(toplevel, child)
            
        def _on_container_add(container, widget):
            self.parse_one(toplevel, widget)
        container.connect('add', _on_container_add)
        
    def GtkDialog(self, toplevel, dialog):
        self.parse_one(toplevel, dialog.action_area)
        self.parse_one(toplevel, dialog.vbox)

    def GtkMenuItem(self, toplevel, item):
        submenu = item.get_submenu()
        if submenu:
            submenu.set_data('parent-menu', item)
            for child_item in submenu.get_children():
                child_item.set_data('parent-menu', item)
            self.parse_one(toplevel, submenu)

