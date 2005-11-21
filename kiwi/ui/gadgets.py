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
#

"""Graphical utilities: color management and eyecandy"""

import gobject
import gtk
from gtk import gdk

from kiwi.decorators import delayed
from kiwi.utils import gsignal, type_register

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


class FadeOut(gobject.GObject):
    """I am a helper class to draw the fading effect of the background
    Call my methods start() and stop() to control the fading.
    """
    gsignal('done')
    gsignal('color-changed', gdk.Color)

    # How long time it'll take before we start (in ms)
    COMPLAIN_DELAY = 500

    MERGE_COLORS_DELAY = 100

    # XXX: Fetch the default value from the widget instead of hard coding it.
    GOOD_COLOR = "white"
    ERROR_COLOR = "#ffd5d5"

    def __init__(self, widget):
        gobject.GObject.__init__(self)
        self._widget = widget
        self._background_timeout_id = -1
        
        # Done is set when animation is already finished.
        # Then the background is normally in another color.
        self._done = False
        
    def _merge_colors(self, src_color, dst_color, steps=10):
        """
        Change the background of widget from src_color to dst_color
        in the number of steps specified
        """
        gdk_src = gdk.color_parse(src_color)
        gdk_dst = gdk.color_parse(dst_color)
        rs, gs, bs = gdk_src.red, gdk_src.green, gdk_src.blue
        rd, gd, bd = gdk_dst.red, gdk_dst.green, gdk_dst.blue
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

    def reset(self):
        self.stop()
        self.emit('color-changed', gdk.color_parse(FadeOut.GOOD_COLOR))
        
    # FIXME: When we can depend on 2.4
    #@delayed(COMPLAIN_DELAY)
    def start(self):
        # If we changed during the delay
        if self._background_timeout_id != -1:
            return
        elif self._done:
            self.emit('done')
            return
        
        self._done = False
        func = self._merge_colors(FadeOut.GOOD_COLOR,
                                  FadeOut.ERROR_COLOR).next
        self._background_timeout_id = (
            gobject.timeout_add(FadeOut.MERGE_COLORS_DELAY, func))
    start = delayed(COMPLAIN_DELAY)(start)
    
    def stop(self):
        """Stops the fadeout and restores the background color"""
        if self._background_timeout_id != -1:
            gobject.source_remove(self._background_timeout_id)
            self._background_timeout_id = -1
        self._widget.update_background(gdk.color_parse(FadeOut.GOOD_COLOR))
        self._done = False

type_register(FadeOut)
