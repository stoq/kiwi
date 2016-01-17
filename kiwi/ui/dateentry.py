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
from kiwi.ui.popup import PopupWindow
from kiwi.utils import gsignal, type_register

_ = lambda m: gettext.dgettext('kiwi', m)

date_converter = converter.get_converter(datetime.date)


class _DateEntryPopup(PopupWindow):

    # We will already have 6 at the bottom because of them buttons padding
    FRAME_PADDING = (6, 0, 6, 6)

    gsignal('date-selected', object)

    def __init__(self, dateentry):
        self._dateentry = dateentry
        super(_DateEntryPopup, self).__init__(dateentry)

    def get_main_widget(self):
        vbox = gtk.VBox()
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

        return self._vbox

    def _on_calendar__day_selected_double_click(self, calendar):
        self.emit('date-selected', self.get_date())

    def _on_select__clicked(self, button):
        self.emit('date-selected', self.get_date())

    def _on_cancel__clicked(self, button):
        self.popdown()

    def _on_today__clicked(self, button):
        self.set_date(datetime.date.today())

    def get_size(self, allocation, monitor):
        return -1, -1

    def popup(self, date):
        """
        Shows the list of options. And optionally selects an item
        :param date: date to select
        """
        popped = super(_DateEntryPopup, self).popup()
        if not popped:
            return False

        if (date is not None and
            date is not ValueUnset):
            self.set_date(date)
        self.grab_focus()

        if not self.calendar.has_focus():
            self.calendar.grab_focus()

    def handle_key_press_event(self, event):
        if event.keyval == keysyms.Tab:
            self.popdown()
            # XXX: private member of dateentry
            self._dateentry._button.grab_focus()
            return True
        return False

    def get_widget_for_popup(self):
        return self._dateentry.entry

    def confirm(self):
        self.emit('date-selected', self.get_date())

    # month in gtk.Calendar is zero-based (i.e the allowed values are 0-11)
    # datetime one-based (i.e. the allowed values are 1-12)
    # So convert between them

    def get_date(self):
        """Gets the date of the date entry
        :returns: date of the entry
        :rtype date: datetime.date
        """
        y, m, d = self.calendar.get_date()
        return datetime.date(y, m + 1, d)

    def set_date(self, date):
        """Sets the date of the date entry
        :param date: date to set
        :type date: datetime.date
        """
        self.calendar.select_month(date.month - 1, date.year)
        self.calendar.select_day(date.day)
        # FIXME: Only mark the day in the current month?
        self.calendar.clear_marks()
        self.calendar.mark_day(date.day)


type_register(_DateEntryPopup)


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
        self._block_changed = False

        # bootstrap problems, kiwi.ui.widgets.entry imports dateentry
        # we need to use a proxy entry because we want the mask
        from kiwi.ui.widgets.entry import ProxyEntry
        self.entry = ProxyEntry()
        # Set datatype before connecting to change event, to not get when the
        # mask is set
        self.entry.set_property('data-type', datetime.date)
        self.entry.connect('changed', self._on_entry__changed)
        self.entry.connect('activate', self._on_entry__activate)
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
        if self._block_changed:
            return
        if self._old_date != date:
            self.emit('changed')
            self._old_date = date

    # Public API

    def set_date(self, date):
        """Sets the date.
        :param date: date to set
        :type date: a datetime.date instance or None
        """
        if not isinstance(date, datetime.date) and date is not None:
            raise TypeError(
                "date must be a datetime.date instance or None, not %r" % (
                    date,))

        if date is None:
            value = ''
        else:
            value = date_converter.as_string(date)

        # We're block the changed call and doing it manually because
        # set_text() triggers a delete-text and then an insert-text,
        # both which are emitting an entry::changed signal
        self._block_changed = True
        self.entry.set_text(value)
        self._block_changed = False

        self._changed(date)

    def get_date(self):
        """Get the selected date
        :returns: the date.
        :rtype: datetime.date or None
        """
        try:
            date = self.entry.read()
        except ValidationError:
            date = None
        if date == ValueUnset:
            date = None
        return date

type_register(DateEntry)
