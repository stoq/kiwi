#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2016 Async Open Source
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
# Author(s): Thiago Bellini <hackedbellini@async.com.br>
#

from gi.repository import Gtk, Gdk


class PopupWindow(Gtk.Window):
    """A generic popup for widgets."""

    PROPAGATE_KEY_PRESS = False
    GRAB_WINDOW = True
    GRAB_ADD = True
    FRAME_PADDING = (2, 2, 2, 2)

    def __init__(self, widget):
        self.visible = False
        self.attached_widget = widget
        super(PopupWindow, self).__init__(type=Gtk.WindowType.POPUP)
        self._setup()

    #
    # Public API
    #

    def confirm(self):
        """Confirm the popup.

        Called when the user activates the popup.
        Subclasses can override this to do something when that happens
        """

    def get_main_widget(self):
        """Get the main widget to attach on the popup.

        Should return a Gtk.Widget to be attached inside the popup.

        :return: a Gtk.Widget
        """
        raise NotImplementedError

    def get_widget_for_popup(self):
        """Get widget used to calculate popup properties.

        Subclasses can override this if they don't want the popup
        size and position to be cauculated using :attr:`.widget`

        :return: the widget used to calculate the popup properties
        """
        return self.attached_widget

    def get_size(self, allocation, monitor):
        """Get the size that should be used for the popup.

        By default the widget's allocation width and -1 for height
        are used.

        :param allocation: the widget allocation
        :param the monitor geometry for the widget window
        :return: (width, height)
        """
        return allocation.width, -1

    def validate_popup(self):
        """Check if we can popup or not."""
        return True

    def adjust_position(self):
        """Adjust the size and position of the popup.

        This is automatically called by :meth:`.popup`, but one
        can call it manually in case the widget which we are
        popping from changed size.
        """
        # width is meant for the popup window
        x, y, width, height = self._get_position()
        self.set_size_request(width, height)
        self.move(x, y)

    def popup(self):
        """Display the popup."""
        if self.visible:
            return False
        if not self.attached_widget.get_realized():
            return False
        if not self.validate_popup():
            return False

        toplevel = self.attached_widget.get_toplevel().get_toplevel()
        if (isinstance(toplevel, (Gtk.Window, Gtk.Dialog)) and
                toplevel.get_group()):
            toplevel.get_group().add_window(self)

        self.show_all()
        self.adjust_position()

        if self.GRAB_WINDOW and not self._popup_grab_window():
            self.hide()
            return False

        if self.GRAB_ADD:
            self.grab_add()

        self.visible = True
        return True

    def popdown(self):
        """Hide the popup."""
        if not self.visible:
            return False
        if not self.attached_widget.get_realized():
            return False

        if self.GRAB_ADD:
            self.grab_remove()

        self.hide()
        self.attached_widget.grab_focus()

        self.visible = False
        return True

    def handle_key_press_event(self, event):
        """Handle a key press event.

        By default, escape and alt + up will make the popup popdown.
        Return, KP_Enter, KP_Space and Tab will make it confirm.
        Subclasses can override this to handle more options.

        :param event: the gdk event
        :returns: ``True`` if the event was handled, ``False`` otherwise
        """
        keyval = event.get_keyval()[1]
        state = event.get_state()
        if state:
            state &= Gtk.accelerator_get_default_mod_mask()

        if (keyval == Gdk.KEY_Escape or
            (state == Gdk.ModifierType.MOD1_MASK and
             (keyval == Gdk.KEY_Up or keyval == Gdk.KEY_KP_Up))):
            self.popdown()
            return True
        elif keyval in [Gdk.KEY_Return,
                        Gdk.KEY_KP_Enter,
                        Gdk.KEY_KP_Space,
                        Gdk.KEY_Tab]:
            self.confirm()
            return True

        return False

    #
    #  Private
    #

    def _setup(self):
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self._on__key_press_event)
        self.connect('button-press-event', self._on__button_press_event)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        self.add(frame)
        frame.show()

        alignment = Gtk.Alignment.new(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(*self.FRAME_PADDING)
        frame.add(alignment)
        alignment.show()

        self.main_widget = self.get_main_widget()
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add(self.main_widget)
        alignment.add(self.main_box)

        self.set_resizable(False)
        self.set_screen(self.attached_widget.get_screen())

    def _popup_grab_window(self):
        activate_time = 0
        window = self.get_window()
        grab_status = Gdk.pointer_grab(window, True,
                                       (Gdk.EventMask.BUTTON_PRESS_MASK |
                                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                                        Gdk.EventMask.POINTER_MOTION_MASK),
                                       None, None, activate_time)
        if grab_status == Gdk.GrabStatus.SUCCESS:
            if Gdk.keyboard_grab(window, True, activate_time) == 0:
                return True
            else:
                window.get_display().pointer_ungrab(activate_time)
                return False

        return False

    def _get_position(self):
        widget = self.get_widget_for_popup()
        allocation = widget.get_allocation()
        if isinstance(widget, Gtk.TextView):
            window = widget.get_window(Gtk.TextWindowType.WIDGET)
        else:
            window = widget.get_window()
        screen = widget.get_screen()
        monitor_num = screen.get_monitor_at_window(window)
        m = screen.get_monitor_geometry(monitor_num)

        x, y = 0, 0
        if not widget.get_has_window():
            x += allocation.x
            y += allocation.y
        x, y = window.get_root_coords(x, y)

        width, height = self.get_size(allocation, m)
        # We need real values for the computation here. If we got -1 for
        # width or height get their values from main_widget since
        main_allocation = self.main_widget.get_allocation()
        if width == -1:
            width = main_allocation.width
        if height == -1:
            height = main_allocation.height

        if x < m.x:
            # Prevent x being outside the left side of the monitor
            x = m.x
        elif x + width > m.x + m.width:
            # Prevent x being outside the right side of the monitor
            x = m.x + m.width - width

        if y + allocation.height + height <= m.y + m.height:
            # If there's enough space, show the right avove the widget
            y += allocation.height
        elif y - height >= m.y:
            # If there's not enough space bellow, show it on top
            y -= height
        elif m.y + m.height - (y + allocation.height) > y - m.y:
            y += allocation.height
            height = m.y + m.height - y
        else:
            height = y - m.y
            y = m.y

        return x, y, width, height

    #
    #  Callbacks
    #

    def _on__key_press_event(self, window, event):
        rv = self.handle_key_press_event(event)

        if not rv and self.PROPAGATE_KEY_PRESS:
            # Let the widget handle the event
            self.attached_widget.event(event)
            rv = True

        return rv

    def _on__button_press_event(self, window, event):
        # If we're clicking outside of the window
        # close the popup
        toplevel = event.window.get_toplevel()
        parent = self.main_widget.get_parent_window()
        if toplevel != parent:
            self.popdown()
            return True

        event_rect = Gdk.Rectangle()
        event_rect.x, event_rect.y = event.get_root_coords()
        event_rect.width = 1
        event_rect.height = 1

        window_rect = Gdk.Rectangle()
        (window_rect.x,
         window_rect.y,
         window_rect.width,
         window_rect.height) = self._get_position()

        intersection = Gdk.rectangle_intersect(event_rect, window_rect)
        # if the click was outside this window, hide it
        if not intersection[0]:
            self.popdown()
            return True

        return False
