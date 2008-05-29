#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006 Async Open Source
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
# Based on date cell renderer in Planner written by Richard Hult
#  and Mikael Hallendal
#

import gettext
import datetime

import gtk
from gtk import gdk, keysyms

from kiwi.datatypes import converter, ValueUnset, ValidationError
from kiwi.utils import gsignal, type_register

_ = lambda m: gettext.dgettext('kiwi', m)

date_converter = converter.get_converter(datetime.date)

class _DateEntryPopup(gtk.Window):
    gsignal('date-selected', object)
    def __init__(self, dateentry):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.add_events(gdk.BUTTON_PRESS_MASK)
        self.connect('key-press-event', self._on__key_press_event)
        self.connect('button-press-event', self._on__button_press_event)
        self._dateentry = dateentry

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.add(frame)
        frame.show()

        vbox = gtk.VBox()
        vbox.set_border_width(6)
        frame.add(vbox)
        vbox.show()
        self._vbox = vbox

        self.calendar = gtk.Calendar()
        self.calendar.connect('day-selected-double-click',
                               self._on_calendar__day_selected_double_click)
        vbox.pack_start(self.calendar, False, False)
        self.calendar.show()

        buttonbox = gtk.HButtonBox()
        buttonbox.set_border_width(6)
        buttonbox.set_layout(gtk.BUTTONBOX_SPREAD)
        vbox.pack_start(buttonbox, False, False)
        buttonbox.show()

        for label, callback in [(_('_Today'), self._on_today__clicked),
                                (_('_Cancel'), self._on_cancel__clicked),
                                (_('_Select'), self._on_select__clicked)]:
            button = gtk.Button(label, use_underline=True)
            button.connect('clicked', callback)
            buttonbox.pack_start(button)
            button.show()

        self.set_resizable(False)
        self.set_screen(dateentry.get_screen())

        self.realize()
        self.height = self._vbox.size_request()[1]

    def _on_calendar__day_selected_double_click(self, calendar):
        self.emit('date-selected', self.get_date())

    def _on__button_press_event(self, window, event):
        # If we're clicking outside of the window close the popup
        hide = False

        # Also if the intersection of self and the event is empty, hide
        # the calendar
        if (tuple(self.allocation.intersect(
              gdk.Rectangle(x=int(event.x), y=int(event.y),
                           width=1, height=1))) == (0, 0, 0, 0)):
            hide = True

        # Toplevel is the window that received the event, and parent is the
        # calendar window. If they are not the same, means the popup should
        # be hidden. This is necessary for when the event happens on another
        # widget
        toplevel = event.window.get_toplevel()
        parent = self.calendar.get_parent_window()
        if toplevel != parent:
            hide = True

        if hide:
            self.popdown()

    def _on__key_press_event(self, window, event):
        """
        Mimics Combobox behavior

        Escape or Alt+Up: Close
        Enter, Return or Space: Select
        """

        keyval = event.keyval
        state = event.state & gtk.accelerator_get_default_mod_mask()
        if (keyval == keysyms.Escape or
            ((keyval == keysyms.Up or keyval == keysyms.KP_Up) and
             state == gdk.MOD1_MASK)):
            self.popdown()
            return True
        elif keyval == keysyms.Tab:
            self.popdown()
            # XXX: private member of dateentry
            self._dateentry._button.grab_focus()
            return True
        elif (keyval == keysyms.Return or
              keyval == keysyms.space or
              keyval == keysyms.KP_Enter or
              keyval == keysyms.KP_Space):
            self.emit('date-selected', self.get_date())
            return True

        return False

    def _on_select__clicked(self, button):
        self.emit('date-selected', self.get_date())

    def _on_cancel__clicked(self, button):
        self.popdown()

    def _on_today__clicked(self, button):
        self.set_date(datetime.date.today())

    def _popup_grab_window(self):
        activate_time = 0L
        if gdk.pointer_grab(self.window, True,
                            (gdk.BUTTON_PRESS_MASK |
                             gdk.BUTTON_RELEASE_MASK |
                             gdk.POINTER_MOTION_MASK),
                             None, None, activate_time) == 0:
            if gdk.keyboard_grab(self.window, True, activate_time) == 0:
                return True
            else:
                self.window.get_display().pointer_ungrab(activate_time);
                return False
        return False

    def _get_position(self):
        self.realize()
        calendar = self

        sample = self._dateentry

        # We need to fetch the coordinates of the entry window
        # since comboentry itself does not have a window
        x, y = sample.entry.window.get_origin()
        width, height = calendar.size_request()
        height = self.height

        screen = sample.get_screen()
        monitor_num = screen.get_monitor_at_window(sample.window)
        monitor = screen.get_monitor_geometry(monitor_num)

        if x < monitor.x:
            x = monitor.x
        elif x + width > monitor.x + monitor.width:
            x = monitor.x + monitor.width - width

        if y + sample.allocation.height + height <= monitor.y + monitor.height:
            y += sample.allocation.height
        elif y - height >= monitor.y:
            y -= height
        elif (monitor.y + monitor.height - (y + sample.allocation.height) >
              y - monitor.y):
            y += sample.allocation.height
            height = monitor.y + monitor.height - y
        else :
            height = y - monitor.y
            y = monitor.y

        return x, y, width, height

    def popup(self, date):
        """
        Shows the list of options. And optionally selects an item
        @param date: date to select
        """
        combo = self._dateentry
        if not (combo.flags() & gtk.REALIZED):
            return

        treeview = self.calendar
        if treeview.flags() & gtk.MAPPED:
            return
        toplevel = combo.get_toplevel()
        if isinstance(toplevel, gtk.Window) and toplevel.group:
            toplevel.group.add_window(self)

        x, y, width, height = self._get_position()
        self.set_size_request(width, height)
        self.move(x, y)
        self.show_all()

        if (date is not None and
            date is not ValueUnset):
            self.set_date(date)
        self.grab_focus()

        if not (self.calendar.flags() & gtk.HAS_FOCUS):
            self.calendar.grab_focus()

        if not self._popup_grab_window():
            self.hide()
            return

        self.grab_add()

    def popdown(self):
        """Hides the list of options"""
        combo = self._dateentry
        if not (combo.flags() & gtk.REALIZED):
            return

        self.grab_remove()
        self.hide_all()

    # month in gtk.Calendar is zero-based (i.e the allowed values are 0-11)
    # datetime one-based (i.e. the allowed values are 1-12)
    # So convert between them

    def get_date(self):
        """Gets the date of the date entry
        @returns: date of the entry
        @rtype date: datetime.date
        """
        y, m, d = self.calendar.get_date()
        return datetime.date(y, m + 1, d)

    def set_date(self, date):
        """Sets the date of the date entry
        @param date: date to set
        @type date: datetime.date
        """
        self.calendar.select_month(date.month - 1, date.year)
        self.calendar.select_day(date.day)
        # FIXME: Only mark the day in the current month?
        self.calendar.clear_marks()
        self.calendar.mark_day(date.day)

class DateEntry(gtk.HBox):
    """I am an entry which you can input a date on.
    In addition to an gtk.Entry I also contain a button
    with an arrow you can click to get popup window with a gtk.Calendar
    for which you can use to select the date
    """
    gsignal('changed')
    gsignal('activate')
    def __init__(self):
        gtk.HBox.__init__(self)

        self._popping_down = False
        self._old_date = None

        # bootstrap problems, kiwi.ui.widgets.entry imports dateentry
        # we need to use a proxy entry because we want the mask
        from kiwi.ui.widgets.entry import ProxyEntry
        self.entry = ProxyEntry()
        self.entry.connect('changed', self._on_entry__changed)
        self.entry.connect('activate', self._on_entry__activate)
        self.entry.set_property('data-type', datetime.date)
        mask = self.entry.get_mask()
        if mask:
            self.entry.set_width_chars(len(mask))
        self.pack_start(self.entry, False, False)
        self.entry.show()

        self._button = gtk.ToggleButton()
        self._button.connect('scroll-event', self._on_entry__scroll_event)
        self._button.connect('toggled', self._on_button__toggled)
        self._button.set_focus_on_click(False)
        self.pack_start(self._button, False, False)
        self._button.show()

        arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
        self._button.add(arrow)
        arrow.show()

        self._popup = _DateEntryPopup(self)
        self._popup.connect('date-selected', self._on_popup__date_selected)
        self._popup.connect('hide', self._on_popup__hide)
        self._popup.set_size_request(-1, 24)

    # Virtual methods

    def do_grab_focus(self):
        self.entry.grab_focus()

    # Callbacks

    def _on_entry__changed(self, entry):
        try:
            date = self.get_date()
        except ValidationError:
            date = None
        self._changed(date)

    def _on_entry__activate(self, entry):
        self.emit('activate')

    def _on_entry__scroll_event(self, entry, event):
        if event.direction == gdk.SCROLL_UP:
            days = 1
        elif event.direction == gdk.SCROLL_DOWN:
            days = -1
        else:
            return

        try:
            date = self.get_date()
        except ValidationError:
            date = None

        if not date:
            newdate = datetime.date.today()
        else:
            newdate = date + datetime.timedelta(days=days)
        self.set_date(newdate)

    def _on_button__toggled(self, button):
        if self._popping_down:
            return

        try:
            date = self.get_date()
        except ValidationError:
            date = None

        self._popup.popup(date)

    def _on_popup__hide(self, popup):
        self._popping_down = True
        self._button.set_active(False)
        self._popping_down = False

    def _on_popup__date_selected(self, popup, date):
        self.set_date(date)
        popup.popdown()
        self.entry.grab_focus()
        self.entry.set_position(len(self.entry.get_text()))
        self._changed(date)

    def _changed(self, date):
        if self._old_date != date:
            self.emit('changed')
            self._old_date = date

    # Public API

    def set_date(self, date):
        """Sets the date.
        @param date: date to set
        @type date: a datetime.date instance or None
        """
        if not isinstance(date, datetime.date) and date is not None:
            raise TypeError(
                "date must be a datetime.date instance or None, not %r" % (
                date,))

        if date is None:
            value = ''
        else:
            value = date_converter.as_string(date)
        self.entry.set_text(value)

    def get_date(self):
        """Get the selected date
        @returns: the date.
        @rtype: datetime.date or None
        """
        try:
            date = self.entry.read()
        except ValidationError:
            date = None
        if date == ValueUnset:
            date = None
        return date

type_register(DateEntry)
