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

def quit_if_last(*args):
    windows = [toplevel
               for toplevel in gtk.window_list_toplevels()
                   if toplevel.get_property('type') == gtk.WINDOW_TOPLEVEL]
    if len(windows) == 1:
        gtk.main_quit()

