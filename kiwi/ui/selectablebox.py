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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""
A box which you can select and will have a border around it when
you click on any widgets in it
"""

import gtk
from gtk import gdk

class SelectableBox(object):
    def __init__(self, width=4):
        self._selected = None
        self._draw_gc = None
        self._selection_width = width
        self.unset_flags(gtk.NO_WINDOW)
        self.set_redraw_on_allocate(True)
        self.set_spacing(width)
        self.set_border_width(width)

    # Public API

    def get_selected(self):
        """
        Get the currently selected widget.
        @returns: widget
        """

        return self._selected

    def set_selected(self, widget):
        """
        Set the widget to be selected, must be a children of self.
        @param widget: widget to select.
        """

        if not widget in self.get_children():
            raise ValueError("widget must be a child of %r" % self)

        old_selected = self._selected
        self._selected = widget
        if old_selected != widget:
            self.queue_draw()

    def pack_start(self, child, expand=True, fill=True, padding=0):
        """
        Identical to gtk.Box.pack_start
        """
        super(SelectableBox, self).pack_start(child, expand=expand,
                                              fill=fill, padding=padding)
        self._child_added(child)

    def pack_end(self, child, expand=True, fill=True, padding=0):
        """
        Identical to gtk.Box.pack_end
        """
        super(SelectableBox, self).pack_end(child, expand=expand,
                                            fill=fill, padding=padding)
        self._child_added(child)

    def add(self, child):
        """
        Identical to gtk.Container.add
        """
        super(SelectableBox, self).add(child)
        self._child_added(child)

    def update_selection(self):
        selected = self._selected
        if not selected:
            return

        border = self._selection_width
        x, y, w, h = selected.allocation
        self.window.draw_rectangle(self._draw_gc, False,
                                   x - (border / 2), y - (border / 2),
                                   w + border, h + border)

    # GtkWidget

    def do_realize(self):
        assert not (self.flags() & gtk.NO_WINDOW)
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(self.get_parent_window(),
                                 width=self.allocation.width,
                                 height=self.allocation.height,
                                 window_type=gdk.WINDOW_CHILD,
                                 wclass=gdk.INPUT_OUTPUT,
                                 event_mask=(self.get_events() |
                                             gdk.EXPOSURE_MASK |
                                             gdk.BUTTON_PRESS_MASK))
        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)

        self._draw_gc = gdk.GC(self.window,
                               line_width=self._selection_width,
                               line_style=gdk.SOLID,
                               foreground=self.style.bg[gtk.STATE_SELECTED])

    def do_button_press_event(self, event):
        selected = self._get_child_at_pos(int(event.x), int(event.y))
        if selected:
            self.set_selected(selected)

    # Private

    def _get_child_at_pos(self, x, y):
        """
        Get child at position x and y.
        @param x: x coordinate
        @type x: integer
        @param y: y coordinate
        @type y: integer
        """
        toplevel = self.get_toplevel()
        for child in self.get_children():
            coords = toplevel.translate_coordinates(child, x, y)
            if not coords:
                continue

            child_x, child_y = coords
            if (0 <= child_x < child.allocation.width and
                0 <= child_y < child.allocation.height and
                child.flags() & (gtk.MAPPED | gtk.VISIBLE)):
                return child

    def _child_added(self, child):
        child.connect('button-press-event',
                      lambda child, e: self.set_selected(child))

class SelectableHBox(SelectableBox, gtk.HBox):
    __gtype_name__ = 'SelectableHBox'

    def __init__(self, width=4):
        gtk.HBox.__init__(self)
        SelectableBox.__init__(self, width=width)

    do_realize = SelectableBox.do_realize
    do_button_press_event = SelectableBox.do_button_press_event

    def do_size_allocate(self, allocation):
        gtk.HBox.do_size_allocate(self, allocation)
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

    def do_expose_event(self, event):
        gtk.HBox.do_expose_event(self, event)
        self.update_selection()

class SelectableVBox(SelectableBox, gtk.VBox):
    __gtype_name__ = 'SelectableVBox'

    def __init__(self, width=4):
        gtk.VBox.__init__(self)
        SelectableBox.__init__(self, width=width)

    do_realize = SelectableBox.do_realize
    do_button_press_event = SelectableBox.do_button_press_event

    def do_size_allocate(self, allocation):
        gtk.VBox.do_size_allocate(self, allocation)
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

    def do_expose_event(self, event):
        gtk.VBox.do_expose_event(self, event)
        self.update_selection()
