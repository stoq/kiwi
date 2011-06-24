#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2008 Async Open Source
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
# Author(s): Ronaldo Maia <romaia@async.com.br>
#
import gtk
import gobject

from kiwi.utils import quote
from kiwi.ui.gadgets import gdk_color_to_string

class ComboDetailsCellRenderer(gtk.GenericCellRenderer):
    """A Cell Renderer for ComboEntry inspired by firefox's awesome bar

    To show some details on each entry of the popup, you should call the method
    ComboEntry.set_details_callback with a callable that expects an object.

    This will be the object that the entry represents if the ComboEntry mode
    is DATA and will be None if the mode is STRING (in which case, details
    don't make sense).
    """

    label = gobject.property(type=str, default="")
    data = gobject.property(type=object)

    def __init__(self):
        label = gtk.Label()
        self._label_layout = label.create_pango_layout('')
        self._details_callback = None

        gtk.GenericCellRenderer.__init__(self)

    def set_details_callback(self, callable):
        self._details_callback = callable

    def on_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):

        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)

        # Center the label
        y_offset = cell_area.height/2 - height/2

        # Draws label
        widget.style.paint_layout(window,
                                 gtk.STATE_ACTIVE, False,
                                 cell_area, widget, "",
                                 cell_area.x + x_offset,
                                 cell_area.y + y_offset,
                                 self._label_layout)

        if not self._details_callback:
            return

        # Draw a separator to easily distinguish between options
        widget.style.paint_hline(window,
                                 gtk.STATE_ACTIVE,
                                 cell_area, widget, "",
                                 cell_area.x, cell_area.x+cell_area.width,
                                 cell_area.y+cell_area.height - 1
                                 )

    def on_get_size(self, widget, cell_area):
        text = quote(self.label)

        if self._details_callback:
            details = self._details_callback(self.data)
            mark_up = '%s\n<span foreground="%s">%s</span>'
            color = gdk_color_to_string(widget.style.fg[gtk.STATE_NORMAL])
            text = mark_up % (self.label, color, details)

        self._label_layout.set_markup(text)
        width, height = self._label_layout.get_pixel_size()

        return 0, 0, width, height + 2


gobject.type_register(ComboDetailsCellRenderer)
