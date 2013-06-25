#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2008-2012 Async Open Source
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

import glib
import gobject
import gtk

from kiwi.ui.gadgets import gdk_color_to_string, draw_editable_border


class EditableTextRenderer(gtk.CellRendererText):
    """Adds a border to an editable text so it can be told apart from not-editable."""

    def do_render(self, drawable, widget, background_area, cell_area, expose_area, flags):
        draw_editable_border(widget, drawable, cell_area)
        gtk.CellRendererText.do_render(self, drawable, widget, background_area,
                                       cell_area, expose_area, flags)


gobject.type_register(EditableTextRenderer)


class EditableSpinRenderer(gtk.CellRendererSpin):
    """Adds a border to an editable spin so it becomes easy to see it is editable."""

    def do_render(self, drawable, widget, background_area, cell_area, expose_area, flags):
        draw_editable_border(widget, drawable, cell_area)
        gtk.CellRendererText.do_render(self, drawable, widget, background_area,
                                       cell_area, expose_area, flags)


gobject.type_register(EditableSpinRenderer)


class ComboDetailsCellRenderer(gtk.CellRenderer):
    """A Cell Renderer for ComboEntry inspired by firefox's awesome bar

    To show some details on each entry of the popup, you should call the method
    ComboEntry.set_details_callback with a callable that expects an object.

    This will be the object that the entry represents if the ComboEntry mode
    is DATA and will be None if the mode is STRING (in which case, details
    don't make sense).
    """

    label = gobject.property(type=str, default="")
    data = gobject.property(type=object)

    def __init__(self, use_markup=False):
        """
        :param use_markup: wheter all strings we send in are already
          in pango markup
        """
        self.use_markup = use_markup
        label = gtk.Label()
        self._label_layout = label.create_pango_layout('')
        self._details_callback = None

        gtk.CellRenderer.__init__(self)

    def set_details_callback(self, callable):
        self._details_callback = callable

    def do_render_gtk2(self, window, widget, background_area, cell_area,
                       expose_area, flags):
        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)

        # Center the label
        y_offset = cell_area.height / 2 - height / 2

        if flags & gtk.CELL_RENDERER_SELECTED:
            state = gtk.STATE_SELECTED
        else:
            state = gtk.STATE_ACTIVE

        # Draws label
        widget.style.paint_layout(window,
                                  state, False,
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
                                 cell_area.x,
                                 cell_area.x + cell_area.width,
                                 cell_area.y + cell_area.height - 1)

    def do_render_gtk3(self, cr, widget, background_area, cell_area, flags):
        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)

        # Center the label
        y_offset = cell_area.height / 2 - height / 2

        # Draws label
        context = widget.get_style_context()
        gtk.render_layout(context, cr,
                          cell_area.x + x_offset,
                          cell_area.y + y_offset,
                          self._label_layout)
        if not self._details_callback:
            return

        gtk.render_line(context, cr,
                        cell_area.x, cell_area.y,
                        cell_area.x + cell_area.width,
                        cell_area.y + cell_area.height - 1)

    if gtk.gtk_version >= (3, 0):
        do_render = do_render_gtk3
    else:
        do_render = do_render_gtk2

    def _escape(self, text):
        if not self.use_markup:
            text = glib.markup_escape_text(text)
        return text

    def do_get_size(self, widget, cell_area):
        if self._details_callback:
            details = self._details_callback(self.data)
            mark_up = '%s\n%s'
            color = gdk_color_to_string(widget.style.fg[gtk.STATE_NORMAL])
            text = mark_up % (self.label, color, self._escape(details))
        else:
            text = self._escape(self.label)

        self._label_layout.set_markup(text)
        width, height = self._label_layout.get_pixel_size()

        return 0, 0, width, height + 2


gobject.type_register(ComboDetailsCellRenderer)
