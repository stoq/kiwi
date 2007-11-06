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

#
# This is tricky and contains quite a few hacks:
# An entry contains 2 GdkWindows, one for the background and one for
# the text area. The normal one, on which the (normally white) background
# is drawn can be accessed through entry.window (after realization)
# The other window is the one where the cursor and the text is drawn upon,
# it's refered to as "text area" inside the GtkEntry code and it is called
# the same here. It can only be accessed through window.get_children()[0],
# since it's considered private to the entry.
#
# +-------------------------------------+
# |                 (1)                 |  (1) parent widget (grey)
# |+----------------(2)----------------+|
# || |-- /-\  |                        ||  (2) entry.window (white)
# || |-  | |  |(4)  (3)                ||
# || |   \-/  |                        ||  (3) text area (transparent)
# |+-----------------------------------+|
# |-------------------------------------|  (4) cursor, black
# |                                     |
# +-------------------------------------|
#
# So, now we want to put an icon in the edge:
# An earlier approached by Lorzeno drew the icon directly on the text area,
# which is not desired since if the text is using the whole width of the
# entry the icon will be drawn on top of the text.
# Now what we want to do is to resize the text area and create a
# new window upon which we can draw the icon.
#
# +-------------------------------------+
# |                                     |  (5) icon window
# |+----------------------------++-----+|
# || |-- /-\  |                 ||     ||
# || |-  | |  |                 || (5) ||
# || |   \-/  |                 ||     ||
# |+----------------------------++-----+|
# |-------------------------------------|
# |                                     |
# +-------------------------------------+
#
# When resizing the text area the cursor and text is not moved into the
# correct position, it'll still be off by the width of the icon window
# To fix this we need to call a private function, gtk_entry_recompute,
# a workaround is to call set_visiblity() which calls recompute()
# internally.
#

"""Provides a helper classes for displaying icons in widgets.

Currently only a L{kiwi.ui.widgets.entry.Entry} and widgets
which embed them, L{kiwi.ui.widgets.spinbutton.SpinButton} and
L{kiwi.ui.comboboxentry.BaseComboBoxEntry}.
"""

import gtk
from gtk import gdk
from kiwi.ui.tooltip import Tooltip

class IconEntry(object):
    """
    Helper object for rendering an icon in a GtkEntry
    """

    def __init__(self, entry):
        if not isinstance(entry, gtk.Entry):
            raise TypeError("entry must be a gtk.Entry")
        self._constructed = False
        self._pixbuf = None
        self._pixw = 1
        self._pixh = 1
        self._text_area = None
        self._text_area_pos = (0, 0)
        self._icon_win = None
        self._entry = entry
        self._tooltip = Tooltip(self)
        self._locked = False
        entry.connect('enter-notify-event',
                      self._on_entry__enter_notify_event)
        entry.connect('leave-notify-event',
                      self._on_entry__leave_notify_event)
        entry.connect('notify::xalign',
                      self._on_entry__notify_xalign)
        self._update_position()

    def _on_entry__notify_xalign(self, entry, pspec):
        self._update_position()

    def _on_entry__enter_notify_event(self, entry, event):
        icon_win = self.get_icon_window()
        if event.window != icon_win:
            return

        self._tooltip.display(entry)

    def _on_entry__leave_notify_event(self, entry, event):
        if event.window != self.get_icon_window():
            return

        self._tooltip.hide()

    def set_tooltip(self, text):
        self._tooltip.set_text(text)

    def get_icon_window(self):
        return self._icon_win

    def set_pixbuf(self, pixbuf):
        """
        Sets a pixbuf or None to reset.
        @param pixbuf: a gdk.Pixbuf or None
        """
        entry = self._entry
        if not isinstance(entry.get_toplevel(), gtk.Window):
            # For widgets in SlaveViews, wait until they're attached
            # to something visible, then set the pixbuf
            entry.connect_object('realize', self.set_pixbuf, pixbuf)
            return

        if pixbuf:
            if not isinstance(pixbuf, gdk.Pixbuf):
                raise TypeError("pixbuf must be a GdkPixbuf")
        else:
            # Turning of the icon should also restore the background
            entry.modify_base(gtk.STATE_NORMAL, None)
            if not self._pixbuf:
                return
        self._pixbuf = pixbuf

        if pixbuf:
            self._pixw = pixbuf.get_width()
            self._pixh = pixbuf.get_height()
        else:
            self._pixw = self._pixh = 0

        win = self._icon_win
        if not win:
            self.construct()
            win = self._icon_win

        self.resize_windows()

        # XXX: Why?
        if win:
            if not pixbuf:
                win.hide()
            else:
                win.show()

        self._recompute()
        entry.queue_draw()

    def construct(self):
        if self._constructed:
            return

        entry = self._entry
        if not entry.flags() & gtk.REALIZED:
            entry.realize()

        # Hack: Save a reference to the text area, now when its created
        self._text_area = entry.window.get_children()[0]
        self._text_area_pos = self._text_area.get_position()

        # PyGTK should allow default values for most of the values here.
        win = gtk.gdk.Window(entry.window,
                             self._pixw, self._pixh,
                             gtk.gdk.WINDOW_CHILD,
                             (gtk.gdk.ENTER_NOTIFY_MASK |
                              gtk.gdk.LEAVE_NOTIFY_MASK),
                             gtk.gdk.INPUT_OUTPUT,
                             'icon window',
                             0, 0,
                             entry.get_visual(),
                             entry.get_colormap(),
                             gtk.gdk.Cursor(entry.get_display(), gdk.LEFT_PTR),
                             '', '', True)
        self._icon_win = win
        win.set_user_data(entry)
        win.set_background(entry.style.base[entry.state])
        self._constructed = True

    def deconstruct(self):
        if self._icon_win:
            # This is broken on PyGTK 2.6.x
            try:
                self._icon_win.set_user_data(None)
            except:
                pass
            # Destroy not needed, called by the GC.
            self._icon_win = None

    def update_background(self, color):
        if self._locked:
            return
        if not self._icon_win:
            return

        self._entry.modify_base(gtk.STATE_NORMAL, color)

        self.draw_pixbuf()

    def get_background(self):
        return self._entry.style.base[gtk.STATE_NORMAL]

    def resize_windows(self):
        if not self._pixbuf:
            return

        icony = iconx = 4

        # Make space for the icon, both windows
        winw = self._entry.window.get_size()[0]
        textw, texth = self._text_area.get_size()
        textw = winw - self._pixw - (iconx + icony)

        if self._pos == gtk.POS_LEFT:
            textx, texty = self._text_area_pos
            textx += iconx + self._pixw

            # FIXME: Why is this needed. Focus padding?
            #        The text jumps without this
            textw -= 2
            self._text_area.move_resize(textx, texty, textw, texth)
            self._recompute()
        elif self._pos == gtk.POS_RIGHT:
            self._text_area.resize(textw, texth)
            iconx += textw

        icon_win = self._icon_win
        # XXX: Why?
        if not icon_win:
            return

        # If the size of the window is large enough, resize and move it
        # Otherwise just move it to the right side of the entry
        if icon_win.get_size() != (self._pixw, self._pixh):
            icon_win.move_resize(iconx, icony, self._pixw, self._pixh)
        else:
            icon_win.move(iconx, icony)

    def draw_pixbuf(self):
        if not self._pixbuf:
            return

        win = self._icon_win
        # XXX: Why?
        if not win:
            return

        # Draw background first
        color = self._entry.style.base_gc[self._entry.state]
        win.draw_rectangle(color, True,
                           0, 0, self._pixw, self._pixh)

        # If sensitive draw the icon, regardless of the window emitting the
        # event since makes it a bit smoother on resize
        if self._entry.flags() & gtk.SENSITIVE:
            win.draw_pixbuf(None, self._pixbuf, 0, 0, 0, 0,
                            self._pixw, self._pixh)

    def _update_position(self):
        if self._entry.get_property('xalign') > 0.5:
            self._pos = gtk.POS_LEFT
        else:
            self._pos = gtk.POS_RIGHT

    def _recompute(self):
        # Protect against re-entrancy when inserting text, happens in DateEntry
        if self._locked:
            return

        self._locked = True

        # Hack: This triggers a .recompute() which is private
        visibility = self._entry.get_visibility()
        self._entry.set_visibility(not visibility)
        self._entry.set_visibility(visibility)

        # Another option would be to call insert_text, however it
        # emits the signal ::changed which is not desirable.
        #self._entry.insert_text('')

        self._locked = False
