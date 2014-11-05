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
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#            Og B. Maciel <ogmaciel@src.gnome.org>
#

"""Graphical utilities: color management and eyecandy"""

import io
import logging
import math

import cairo
import gobject
import gtk
from gtk import gdk

from kiwi.utils import gsignal, type_register
from kiwi.ui.pixbufutils import pixbuf_from_string


def gdk_color_to_string(color):
    """Convert a color to a #AABBCC string"""
    return "#%02X%02X%02X" % (int(color.red) >> 8,
                              int(color.green) >> 8,
                              int(color.blue) >> 8)


def set_foreground(widget, color, state=gtk.STATE_NORMAL):
    """
    Set the foreground color of a widget:

      - widget: the widget we are changing the color
      - color: a hexadecimal code or a well known color name
      - state: the state we are afecting, see gtk.STATE_*
    """
    widget.modify_fg(state, gdk.color_parse(color))


def get_foreground(widget, state=gtk.STATE_NORMAL):
    """Return the foreground color of the widget as a string"""
    style = widget.get_style()
    color = style.fg[state]
    return gdk_color_to_string(color)


def set_background(widget, color, state=gtk.STATE_NORMAL):
    """
    Set the background color of a widget:

      - widget: the widget we are changing the color
      - color: a hexadecimal code or a well known color name
      - state: the state we are afecting, see gtk.STATE_*
    """
    if isinstance(widget, gtk.Entry):
        widget.modify_base(state, gdk.color_parse(color))
    else:
        widget.modify_bg(state, gdk.color_parse(color))


def get_background(widget, state=gtk.STATE_NORMAL):
    """Return the background color of the widget as a string"""
    style = widget.get_style()
    color = style.bg[state]
    return gdk_color_to_string(color)


def quit_if_last(*args):
    windows = [toplevel
               for toplevel in gtk.window_list_toplevels()
               if toplevel.get_property('type') == gtk.WINDOW_TOPLEVEL]
    if len(windows) == 1:
        gtk.main_quit()


def _select_notebook_tab(widget, event, notebook):
    val = event.keyval - 48
    if event.state & gdk.MOD1_MASK and 1 <= val <= 9:
        notebook.set_current_page(val - 1)


def register_notebook_shortcuts(dialog, notebook):
    dialog.toplevel.connect('key-press-event', _select_notebook_tab, notebook)


class FadeOut(gobject.GObject):
    """I am a helper class to draw the fading effect of the background
    Call my methods start() and stop() to control the fading.
    """
    gsignal('done')
    gsignal('color-changed', gdk.Color)

    # How long time it'll take before we start (in ms)
    COMPLAIN_DELAY = 500

    MERGE_COLORS_DELAY = 100

    ERROR_COLOR = "#ffd5d5"

    def __init__(self, widget):
        gobject.GObject.__init__(self)
        self._widget = widget
        self._start_color = None
        self._background_timeout_id = -1
        self._countdown_timeout_id = -1
        self._log = logging.getLogger('fade')
        self._done = False

    def _merge_colors(self, src_color, dst_color, steps=10):
        """
        Change the background of widget from src_color to dst_color
        in the number of steps specified
        """

        self._log.debug('_merge_colors: %s -> %s' % (src_color, dst_color))

        if not src_color:
            yield False

        rs, gs, bs = src_color.red, src_color.green, src_color.blue
        rd, gd, bd = dst_color.red, dst_color.green, dst_color.blue
        rinc = (rd - rs) / float(steps)
        ginc = (gd - gs) / float(steps)
        binc = (bd - bs) / float(steps)
        for dummy in xrange(steps):
            rs += rinc
            gs += ginc
            bs += binc
            col = gdk.color_parse("#%02X%02X%02X" % (int(rs) >> 8,
                                                     int(gs) >> 8,
                                                     int(bs) >> 8))
            self.emit('color-changed', col)
            yield True

        self.emit('done')
        self._background_timeout_id = -1
        self._done = True
        yield False

    def _start_merging(self):
        # If we changed during the delay
        if self._background_timeout_id != -1:
            self._log.debug('_start_merging: Already running')
            return

        self._log.debug('_start_merging: Starting')
        func = self._merge_colors(self._start_color,
                                  gdk.color_parse(FadeOut.ERROR_COLOR)).next
        self._background_timeout_id = (
            gobject.timeout_add(FadeOut.MERGE_COLORS_DELAY, func))
        self._countdown_timeout_id = -1

    def start(self, color):
        """Schedules a start of the countdown.
        :param color: initial background color
        :returns: True if we could start, False if was already in progress
        """
        if self._background_timeout_id != -1:
            self._log.debug('start: Background change already running')
            return False
        if self._countdown_timeout_id != -1:
            self._log.debug('start: Countdown already running')
            return False
        if self._done:
            self._log.debug('start: Not running, already set')
            return False

        self._start_color = color
        self._log.debug('start: Scheduling')
        self._countdown_timeout_id = gobject.timeout_add(
            FadeOut.COMPLAIN_DELAY, self._start_merging)

        return True

    def stop(self):
        """Stops the fadeout and restores the background color"""
        self._log.debug('Stopping')
        if self._background_timeout_id != -1:
            gobject.source_remove(self._background_timeout_id)
            self._background_timeout_id = -1
        if self._countdown_timeout_id != -1:
            gobject.source_remove(self._countdown_timeout_id)
            self._countdown_timeout_id = -1

        self._widget.update_background(self._start_color)
        self._done = False

type_register(FadeOut)

_pixbuf_cache = {}


def draw_editable_border(widget, drawable, cell_area):
    """Draws a border around a widget, signalizing that it is editable"""
    cr = drawable.cairo_create()
    cr.set_line_width(0.5)
    cr.rectangle(cell_area.x, cell_area.y,
                 cell_area.width, cell_area.height)

    style = widget.get_style()
    # The gtk documentation says the dark colors are slightly darker than
    # the bg colors and used for creating shadows. That's perfect here since
    # it will indicate that the border is editable and won't "vanish"
    # when the row is really activated
    cr.set_source_color(style.dark[gtk.STATE_SELECTED])
    cr.stroke()


# Based on code from BillReminder by Og Maciel and
# http://cairographics.org/cookbook/roundedrectangles/

def render_pixbuf(color_name, width=16, height=16, radius=4):
    pixbuf = _pixbuf_cache.get(color_name)
    if pixbuf is not None:
        return pixbuf

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)

    if color_name:
        pi2 = math.pi / 2
        cr.new_sub_path()
        cr.arc(radius, radius, radius, math.pi, 3 * pi2)
        cr.arc(height - radius, radius, radius, 3 * pi2, 4 * pi2)
        cr.arc(height - radius, width - radius, radius, 0, pi2)
        cr.arc(radius, width - radius, radius, pi2, math.pi)
        cr.close_path()

        color = gtk.gdk.color_parse(color_name)
        cr.set_source_rgb(
            float(color.red) / 65536,
            float(color.green) / 65536,
            float(color.blue) / 65536)
    else:
        cr.set_source_rgba(0, 0, 0, 0.0)

    cr.fill_preserve()
    cr.set_source_rgba(0, 0, 0, 0.5)

    cr.set_line_width(1)
    cr.stroke()

    buf = io.BytesIO()
    surface.write_to_png(buf)

    buf.seek(0)
    pixbuf = pixbuf_from_string(buf.getvalue())

    _pixbuf_cache[color_name] = pixbuf
    return pixbuf
