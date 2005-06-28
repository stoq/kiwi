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

import gtk

def gdk_color_to_string(color):
    """Convert a color to a #AABBCC string"""
    return rgb_color_to_string(color.red, color.green, color.blue)

def rgb_color_to_string(red, green, blue):
    """Red green and blue should be in the 0-65535 range"""
    return "#%02X%02X%02X" % (red >> 8, green >> 8, blue >> 8)
    
def set_foreground(widget, color, state=gtk.STATE_NORMAL):
    """
    Set the foreground color of a widget:

      - widget: the widget we are changing the color
      - color: a hexadecimal code or a well known color name
      - state: the state we are afecting, see gtk.STATE_*
    """
    widget.modify_fg(state, gtk.gdk.color_parse(color))

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
        widget.modify_base(state, gtk.gdk.color_parse(color))
    else:
        widget.modify_bg(state, gtk.gdk.color_parse(color))

def get_background(widget, state=gtk.STATE_NORMAL):
    """Return the background color of the widget as a string"""
    style = widget.get_style()
    color = style.bg[state]
    return gdk_color_to_string(color)

def merge_colors(widget, src_color, dst_color, steps=10):
    """Change the background of widget from src_color to dst_color
    in the number of steps specified
    """
    gdk_src = gtk.gdk.color_parse(src_color)
    gdk_dst = gtk.gdk.color_parse(dst_color)
    rs, gs, bs = gdk_src.red, gdk_src.green, gdk_src.blue
    rd, gd, bd = gdk_dst.red, gdk_dst.green, gdk_dst.blue
    rinc = (rd - rs) / float(steps)
    ginc = (gd - gs) / float(steps)
    binc = (bd - bs) / float(steps)
    for dummy in xrange(steps):
        rs += rinc
        gs += ginc
        bs += binc
        color = rgb_color_to_string(int(rs), int(gs), int(bs))
        set_background(widget, color)
        yield True

    yield False

def quit_if_last(*args):
    windows = [toplevel
               for toplevel in gtk.window_list_toplevels()
                   if toplevel.get_property('type') == gtk.WINDOW_TOPLEVEL]
    if len(windows) == 1:
        gtk.main_quit()

