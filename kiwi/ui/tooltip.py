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

"""A tooltip popup window which only pop ups on demand, which
makes it possible for us to tie it to a specific gtk.gdk.Window
"""

import gobject
import gtk

DEFAULT_DELAY = 500
BORDER_WIDTH = 4


class Tooltip(gtk.Window):
    def __init__(self, widget):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        # from gtktooltips.c:gtk_tooltips_force_window
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_name("gtk-tooltips")
        self.set_border_width(BORDER_WIDTH)
        self.connect('expose-event', self._on__expose_event)

        self._label = gtk.Label()
        self.add(self._label)
        self._show_timeout_id = -1

    # from gtktooltips.c:gtk_tooltips_draw_tips
    def _calculate_pos(self, widget):
        screen = widget.get_screen()

        w, h = self.size_request()

        x, y = widget.window.get_origin()

        if widget.flags() & gtk.NO_WINDOW:
            x += widget.allocation.x
            y += widget.allocation.y

        x = screen.get_root_window().get_pointer()[0]
        x -= (w / 2 + BORDER_WIDTH)

        pointer_screen, px, py, _ = screen.get_display().get_pointer()
        if pointer_screen != screen:
            px = x
            py = y

        monitor_num = screen.get_monitor_at_point(px, py)
        monitor = screen.get_monitor_geometry(monitor_num)

        if (x + w) > monitor.x + monitor.width:
            x -= (x + w) - (monitor.x + monitor.width)
        elif x < monitor.x:
            x = monitor.x

        if ((y + h + widget.allocation.height + BORDER_WIDTH) >
            monitor.y + monitor.height):
            y = y - h - BORDER_WIDTH
        else:
            y = y + widget.allocation.height + BORDER_WIDTH

        return x, y

    # from gtktooltips.c:gtk_tooltips_paint_window
    def _on__expose_event(self, window, event):
        w, h = window.size_request()
        window.style.paint_flat_box(window.window,
                                    gtk.STATE_NORMAL, gtk.SHADOW_OUT,
                                    None, window, "tooltip",
                                    0, 0, w, h)
        return False

    def _real_display(self, widget):
        x, y = self._calculate_pos(widget)

        self.move(x, y)
        self.show_all()

    # Public API

    def set_text(self, text):
        self._label.set_text(text)

    def hide(self):
        gtk.Window.hide(self)
        gobject.source_remove(self._show_timeout_id)
        self._show_timeout_id = -1

    def display(self, widget):
        if not self._label.get_text():
            return

        if self._show_timeout_id != -1:
            return

        self._show_timeout_id = gobject.timeout_add(DEFAULT_DELAY,
                                                    self._real_display,
                                                    widget)
