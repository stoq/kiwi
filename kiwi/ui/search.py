#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2007 Async Open Source
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

"""
Search related widgets
"""

import datetime
from decimal import Decimal
import gettext
import sys

import gobject
import gtk

from kiwi.component import implements
from kiwi.datatypes import currency
from kiwi.db.query import (NumberQueryState, StringQueryState,
                           DateQueryState, DateIntervalQueryState,
                           NumberIntervalQueryState, QueryExecuter)
from kiwi.enums import SearchFilterPosition
from kiwi.interfaces import ISearchFilter
from kiwi.python import enum
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.objectlist import ObjectList, SummaryLabel, SearchColumn
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.entry import ProxyDateEntry
from kiwi.utils import gsignal

_ = lambda m: gettext.dgettext('kiwi', m)


#
# Date Search Options
#

class DateSearchOption(object):
    """
    Base class for Date search options
    A date search option is an interval of dates
    @cvar name: name of the search option
    """
    name = None

    def get_today_date(self):
        return datetime.date.today()

    def get_interval(self):
        """
        Get start and end date.
        @returns: start date, end date
        @rtype: datetime.date tuple
        """

class Any(DateSearchOption):
    name = _('Any')

    def get_interval(self):
        return None, None


class Today(DateSearchOption):
    name = _('Today')

    def get_interval(self):
        today = self.get_today_date()
        return today, today


class Yesterday(DateSearchOption):
    name = _('Yesterday')

    def get_interval(self):
        yesterday = self.get_today_date() - datetime.timedelta(days=1)
        return yesterday, yesterday


class LastWeek(DateSearchOption):
    name = _('Last week')

    def get_interval(self):
        today = self.get_today_date()
        return (today - datetime.timedelta(days=7), today)


class LastMonth(DateSearchOption):
    name = _('Last month')

    def get_interval(self):
        today = self.get_today_date()
        year = today.year
        month = today.month - 1
        if not month:
            month = 12
            year -= 1
        # Try 31 first then remove one until date() does not complain.
        day = today.day
        while True:
            try:
                start_date = datetime.date(year, month, day)
                break
            except ValueError:
                day -= 1
        return start_date, self.get_today_date()


class FixedIntervalSearchOption(DateSearchOption):
    start = None
    end = None

    def get_interval(self):
        return self.start, self.end


class FixedDateSearchOption(DateSearchOption):
    date = None

    def get_interval(self):
        return self.date, self.date


#
#   Number Search Options
#

class NumberSearchOption(object):
    """
    Base class for Number search options
    A number search option is an interval of numbers
    @cvar name: name of the search option
    @cvar numbers: how many numbers must the user input: 0, 1 or 2
    """
    name = None
    numbers = 0

    def get_interval(self, start, end):
        """
        Get start and end interval.
        @returns: start, end
        """

class Between(NumberSearchOption):
    name = _('Between')
    numbers = 2

    def get_interval(self, start, end):
        return (start, end)


class EqualsTo(NumberSearchOption):
    name = _('Equals to')
    numbers = 1

    def get_interval(self, start, end):
        return (start, start)


class GreaterThan(NumberSearchOption):
    name = _('Greater or Equal')
    numbers = 1

    def get_interval(self, start, end):
        return (start, None)


class LowerThan(NumberSearchOption):
    name = _('Lower or Equal')
    numbers = 1

    def get_interval(self, start, end):
        return (None, start)


#
#   String Search Options
#

class StringSearchOption(object):
    pass


class Contains(StringSearchOption):
    name = _('Contains')
    mode = StringQueryState.CONTAINS


class DoesNotContain(StringSearchOption):
    name = _('Does Not Contain')
    mode = StringQueryState.NOT_CONTAINS


#
# Search Filters
#

class SearchFilter(gtk.HBox):
    """
    A base classed used by common search filters
    """
    label = gobject.property(type=str, flags=(gobject.PARAM_READWRITE |
                                              gobject.PARAM_CONSTRUCT_ONLY))
    gsignal('changed')
    gsignal('removed')

    implements(ISearchFilter)

    def __init__(self, label=''):
        self.__gobject_init__(label=label)
        self._label = label
        self._remove_button = None

    def _add_remove_button(self):
        self._remove_button = SearchFilterButton(stock=gtk.STOCK_REMOVE)
        self._remove_button.set_relief(gtk.RELIEF_NONE)
        self._remove_button.set_label_visible(False)
        self._remove_button.connect('clicked', self._on_remove_clicked)
        self._remove_button.show()
        self.pack_start(self._remove_button, False, False)

    def _on_remove_clicked(self, button):
        self.emit('removed')

    def do_set_property(self, pspec, value):
        if pspec.name == 'label':
            self._label = value
        else:
            raise AssertionError(pspec.name)

    def do_get_property(self, child, property_id, pspec):
        if pspec.name == 'label':
            return self._label
        else:
            raise AssertionError(pspec.name)

    def set_label(self, label):
        self._label = label

    def get_state(self):
        """
        Implement this in a subclass
        """
        raise NotImplementedError

    def get_title_label(self):
        raise NotImplementedError

    def get_mode_combo(self):
        raise NotImplementedError

    def get_description(self):
        """Returns a description of the search filter.
        @returns: a string describing the search filter.
        """
        raise NotImplementedError

    def set_removable(self):
        if self._remove_button is None:
            self._add_remove_button()


class DateSearchFilter(SearchFilter):
    """
    A filter which helps you to search by a date interval.
    Can be customized through add_option.
    """
    __gtype_name__ = 'DateSearchFilter'
    class Type(enum):
        (USER_DAY,
         USER_INTERVAL) = range(100, 102)

    def __init__(self, label=''):
        """
        Create a new DateSearchFilter object.
        @param label: name of the search filter
        """
        self._options = {}
        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self.mode = ProxyComboBox()
        self.mode.connect(
            'content-changed',
            self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.from_label = gtk.Label(_("From:"))
        self.pack_start(self.from_label, False, False)
        self.from_label.show()

        self.start_date = ProxyDateEntry()
        self._start_changed_id = self.start_date.connect(
            'content-changed', self._on_start_date__changed)
        self.pack_start(self.start_date, False, False, 6)
        self.start_date.show()

        self.to_label = gtk.Label(_("To:"))
        self.pack_start(self.to_label, False, False)
        self.to_label.show()

        self.end_date = ProxyDateEntry()
        self._end_changed_id = self.end_date.connect(
            'content-changed', self._on_end_date__changed)
        self.pack_start(self.end_date, False, False, 6)
        self.end_date.show()

        self.add_custom_options()

        for option in (Any, Today, Yesterday, LastWeek, LastMonth):
            self.add_option(option)

        self.mode.select_item_by_position(0)

    #
    # SearchFilter
    #

    def get_state(self):
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if start == end:
            return DateQueryState(filter=self, date=start)
        return DateIntervalQueryState(filter=self, start=start, end=end)

    def set_state(self, start, end=None):
        self.start_date.set_date(start)
        if end is not None:
            self.end_date.set_date(end)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = ''
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        if start_date:
            if end_date and start_date != end_date:
                desc += ' %s %s %s %s' % (_(u'from'), start_date.strftime('%x'),
                                          _(u'to'), end_date.strftime('%x'),)

            else:
                 desc += start_date.strftime('%x')
        if desc:
            return '%s %s' % (self.get_title_label().get_text(), desc,)

    #
    # Public API
    #

    def clear_options(self):
        """
        Removes all previously added options
        """
        self._options = {}
        self.mode.clear()

    def add_option(self, option_type, position=-2):
        """
        Adds a date option
        @param option_type: option to add
        @type option_type: a L{DateSearchOption} subclass
        """
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option

    def add_option_fixed(self, name, date, position=-2):
        """
        Adds a fixed option, eg one for which date is not
        possible to modify.
        @param name: name of the option
        @param date: fixed data
        @param position: position to add the option at
        """
        option_type = type('', (FixedDateSearchOption,),
                           dict(name=name, date=date))
        self.add_option(option_type, position=position)


    def add_option_fixed_interval(self, name, start, end, position=-2):
        """
        Adds a fixed option interval, eg one for which the dates are not
        possible to modify.
        @param name: name of the option
        @param start: start of the fixed interval
        @param end: end of the fixed interval
        @param position: position to add the option at
        """
        option_type = type('', (FixedIntervalSearchOption,),
                           dict(name=name, start=start, end=end))
        self.add_option(option_type, position=position)

    def add_custom_options(self):
        """Adds the custom options 'Custom day' and 'Custom interval' which
        let the user define its own interval dates.
        """
        pos = len(self.mode) + 1
        for name, option_type in [
            (_('Custom day'), DateSearchFilter.Type.USER_DAY),
            (_('Custom interval'), DateSearchFilter.Type.USER_INTERVAL)]:

            self.mode.insert_item(pos, name, option_type)
            pos += 1

    def get_start_date(self):
        """
        Get the start date.
        @returns: start date
        @rtype: datetime.date or None
        """
        return self.start_date.get_date()

    def get_end_date(self):
        """
        Get the end date.
        @returns: end date
        @rtype: datetime.date or None
        """
        return self.end_date.get_date()

    def set_use_date_entries(self, use_date_entries):
        """
        Toggles the visibility of the user selectable date entries
        @param use_date_entries:
        """
        self.from_label.props.visible = use_date_entries
        self.to_label.props.visible = use_date_entries
        self.start_date.props.visible = use_date_entries
        self.end_date.props.visible = use_date_entries

    def select(self, data=None, position=None):
        """
        selects an item in the combo
        Data or position can be sent in. If nothing
        is sent in the first item will be selected, if any

        @param data: data to select
        @param position: position of data to select
        """
        if data is not None and position is not None:
            raise TypeError("You can't send in both data and position")

        if data is None and position is None:
            position = 0

        if position is not None:
            if len(self.mode):
                self.mode.select_item_by_position(position)
        elif data:
            self.mode.select(data)

    #
    # Private
    #

    def _update_dates(self):
        # This is called when we change mode
        date_type = self.mode.get_selected_data()
        if date_type is None:
            return

        # If we switch to a user selectable day, make sure that
        # both dates are set to today
        if date_type == DateSearchFilter.Type.USER_DAY:
            today = datetime.date.today()
            self.start_date.set_date(today)
            self.end_date.set_date(today)
        # And for user interval, set start to today and to tomorrow
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            today = datetime.date.today()
            self.start_date.set_date(today)
            self.end_date.set_date(today + datetime.timedelta(days=1))
        # Finally for pre-defined ones let the DateSearchOption decide what the
        # values are going to be, these dates are not user editable so
        # we don't need to do any checking.
        else:
            option = self._options.get(date_type)
            assert option, (date_type, self._options)
            start_date, end_date = option.get_interval()
            self.start_date.set_date(start_date)
            self.end_date.set_date(end_date)

    def _update_sensitivity(self):
        date_type = self.mode.get_selected_data()
        enabled = date_type == DateSearchFilter.Type.USER_INTERVAL
        self.to_label.set_sensitive(enabled)
        self.end_date.set_sensitive(enabled)

        enabled = (date_type == DateSearchFilter.Type.USER_INTERVAL or
                   date_type == DateSearchFilter.Type.USER_DAY)
        self.from_label.set_sensitive(enabled)
        self.start_date.set_sensitive(enabled)

    def _internal_set_start_date(self, date):
        self.start_date.handler_block(self._start_changed_id)
        self.start_date.set_date(date)
        self.start_date.handler_unblock(self._start_changed_id)

    def _internal_set_end_date(self, date):
        self.end_date.handler_block(self._end_changed_id)
        self.end_date.set_date(date)
        self.end_date.handler_unblock(self._end_changed_id)

    def _restore_date_validation(self):
        self.start_date.set_valid()
        self.end_date.set_valid()

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, mode):
        self._update_dates()
        self._update_sensitivity()
        self._restore_date_validation()
        self.emit('changed')

    def _on_start_date__changed(self, start_date):
        date_type = self.mode.get_selected_data()
        start = start_date.get_date()
        # For user days, just make sure that the date entries
        # always are in sync
        if date_type == DateSearchFilter.Type.USER_DAY:
            if start is None:
                self.start_date.set_invalid(_(u'Invalid date'))
            else:
                self.start_date.set_valid()
                self._internal_set_end_date(start)
        # Make sure that we cannot select a start date after
        # the end date, be nice and increase the end date if
        # the start date happen to be the same
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            end = self.end_date.get_date()
            if start is None:
                self.start_date.set_invalid(_(u'Invalid date'))
                return
            if end and start >= end:
                self._internal_set_end_date(start + datetime.timedelta(days=1))

            self.start_date.set_valid()

    def _on_end_date__changed(self, end_date):
        date_type = self.mode.get_selected_data()
        # We don't need to do anything for user day, since
        # this the end date widget is disabled
        if date_type == DateSearchFilter.Type.USER_DAY:
            pass
        # Make sure that we cannot select an end date before
        # the start date, be nice and decrease the start date if
        # the end date happen to be the same
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            start = self.start_date.get_date()
            end = end_date.get_date()
            if end is None:
                self.end_date.set_invalid(_(u'Invalid date'))
            else:
                self.end_date.set_valid()

            if start and end and end <= start:
                self._internal_set_start_date(end - datetime.timedelta(days=1))


class ComboSearchFilter(SearchFilter):
    """
    - a label
    - a combo with a set of predefined item to select from
    """
    __gtype_name__ = 'ComboSearchFilter'

    def __init__(self, label='', values=None):
        """
        Create a new ComboSearchFilter object.
        @param name: name of the search filter
        @param values: items to put in the combo, see
            L{kiwi.ui.widgets.combo.ProxyComboBox.prefill}
        """
        SearchFilter.__init__(self, label=label)
        label = gtk.Label(label)
        self.pack_start(label, False, False)
        label.show()
        self.title_label = label

        self.combo = ProxyComboBox()
        if values:
            self.combo.prefill(values)
        self.combo.connect('content-changed', self._on_combo__content_changed)
        self.pack_start(self.combo, False, False, 6)
        self.combo.show()

    #
    # SearchFilter
    #

    def get_state(self):
        value = self.combo.get_selected_data()
        state = NumberQueryState(filter=self,
                                 value=value)
        if hasattr(value, 'id'):
            state.value_id = value.id
            state.value = None
        return state

    def set_state(self, value, value_id=None):
        if value_id is not None:
            for item in self.combo.get_model_items().values():
                if item is None:
                    continue
                if item.id == value_id:
                    value = item
                    break
        self.select(value)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.combo

    def get_description(self):
        desc = ''
        data = self.combo.get_selected_data()
        if data is not None:
            desc += self.combo.get_selected_label()
            return '%s %s' % (self.title_label.get_text(), desc,)

    #
    # Public API
    #

    def select(self, data):
        """
        selects an item in the combo
        @param data: what to select
        """
        self.combo.select(data)

    #
    # Callbacks
    #

    def _on_combo__content_changed(self, mode):
        self.emit('changed')


# Ported from evolution
# Replace with GtkEntry::placeholder-text in Gtk 3.2
class HintedEntry(gtk.Entry):
    def __init__(self):
        gtk.Entry.__init__(self)
        self._hint_shown = False
        self._hint = None

    def set_hint(self, text):
        self._hint = text
        if self._hint_shown:
            gtk.Entry.set_text(self, text)

    def set_text(self, text):
        if not text and not self.has_focus():
            self.show_hint()
        else:
            self.show_text(text)

    def get_text(self):
        text = ""
        if not self._hint_shown:
            text = gtk.Entry.get_text(self)
        return text

    def show_hint(self):
        self._hint_shown = True
        gtk.Entry.set_text(self, self._hint)
        self.modify_text(gtk.STATE_NORMAL,
                         self.get_style().text[gtk.STATE_INSENSITIVE])

    def show_text(self, text):
        self._hint_shown = False
        gtk.Entry.set_text(self, text)
        self.modify_text(gtk.STATE_NORMAL, None)

    def do_grab_focus(self):
        chain = gtk.Entry
        if self._hint_shown:
            chain = gtk.Entry.__base__
        chain.do_grab_focus(self)

    def do_focus_in_event(self, event):
        if self._hint_shown:
            self.show_text("")
        return gtk.Entry.do_focus_in_event(self, event)

    def do_focus_out_event(self, event):
        text = self.get_text()
        if not text:
            self.show_hint()
        return gtk.Entry.do_focus_out_event(self, event)


gobject.type_register(HintedEntry)

class StringSearchFilter(SearchFilter):
    """
    - a label
    - an entry
    @ivar entry: the entry
    @ivar label: the label
    """
    def __init__(self, label, chars=0):
        """
        Create a new StringSearchFilter object.
        @param label: label of the search filter
        @param chars: maximum number of chars used by the search entry
        """
        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self._options = {}
        self.mode = ProxyComboBox()
        self.mode.connect('content-changed', self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)

        self.entry = HintedEntry()
        self.entry.set_hint(_("Search"))
        self.entry.show_hint()
        self.entry.props.secondary_icon_sensitive = False
        self.entry.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY,
                                       gtk.STOCK_FIND)
        self.entry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                       gtk.STOCK_CLEAR)
        self.entry.set_icon_tooltip_text(gtk.ENTRY_ICON_SECONDARY,
                                         _("Clear the search"))
        self.entry.connect("icon-release", self._on_entry__icon_release)
        self.entry.connect('activate', self._on_entry__activate)
        self.entry.connect('changed', self._on_entry__changed)
        if chars:
            self.entry.set_width_chars(chars)
        self.pack_start(self.entry, False, False, 6)
        self.entry.show()

        for option in (Contains, DoesNotContain):
            self._add_option(option)
        self.mode.select_item_by_position(0)

    def _add_option(self, option_type, position=-2):
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, combo):
        self.emit('changed')

    def _on_entry__activate(self, entry):
        self.emit('changed')

    def _on_entry__changed(self, entry):
        entry.props.secondary_icon_sensitive = bool(entry.get_text())

    def _on_entry__icon_release(self, entry, icon_pos, event):
        if icon_pos == gtk.ENTRY_ICON_SECONDARY:
            entry.set_text("")
            entry.grab_focus()
            self.emit('changed')

    #
    # SearchFilter
    #

    def get_state(self):
        option = self.mode.get_selected_data()
        return StringQueryState(filter=self,
                                text=self.entry.get_text(),
                                mode=option.mode)

    def set_state(self, text, mode=None):
        self.entry.set_text(text)
        if mode is not None:
            self.mode.select_item_by_position(mode)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = self.entry.get_text()
        if desc:
            mode = self.mode.get_selected_label()
            return '%s %s "%s"' % (self.title_label.get_text(), mode, desc,)

    #
    # Public API
    #

    def enable_advaced(self):
        self.mode.show()

    def set_label(self, label):
        self.title_label.set_text(label)


class NumberSearchFilter(SearchFilter):
    """
    A filter which helps you to search by a number interval.
    """
    __gtype_name__ = 'NumberSearchFilter'

    def __init__(self, label=''):
        """
        Create a new NumberSearchFilter object.
        @param label: name of the search filter
        """

        self._options = {}

        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.title_label.set_alignment(1.0, 0.5)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self.mode = ProxyComboBox()
        self.mode.connect('content-changed', self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.start = gtk.SpinButton(climb_rate=1.0)
        self.start.get_adjustment().step_increment = 1.0
        self.start.set_range(-sys.maxint-1, sys.maxint)
        self.pack_start(self.start, False, False, 6)
        self.start.show()
        self.start.connect_after('activate', self._on_entry__activate)

        self.and_label = gtk.Label(_("And"))
        self.pack_start(self.and_label, False, False)
        self.and_label.show()

        self.end = gtk.SpinButton(climb_rate=1.0)
        self.end.get_adjustment().step_increment = 1.0
        self.end.set_range(-sys.maxint-1, sys.maxint)
        self.pack_start(self.end, False, False, 6)
        self.end.show()
        self.end.connect_after('activate', self._on_entry__activate)

        for option in (LowerThan, EqualsTo, GreaterThan, Between):
            self.add_option(option)

        self.mode.select_item_by_position(0)

    def set_digits(self, digits):
        """
        Number of decimal place to be displayed
        @param digits: number of decimal places
        """
        self.start.set_digits(digits)
        self.end.set_digits(digits)

    #
    #   Private
    #

    def _update_visibility(self):
        option = self.mode.get_selected_data()
        numbers = option.numbers
        if numbers == 0:
            self.start.hide()
            self.and_label.hide()
            self.end.hide()
        elif numbers == 1:
            self.start.show()
            self.and_label.hide()
            self.end.hide()
        elif numbers == 2:
            self.start.show()
            self.and_label.show()
            self.end.show()


    #
    #   Callbacks
    #

    def _on_entry__activate(self, entry):
        self.emit('changed')

    def _on_mode__content_changed(self, combo):
        self._update_visibility()
        self.emit('changed')

    #
    #   SearchFilter
    #

    def get_state(self):
        # Using Decimals for better precision.
        start_value = Decimal("%.2f" % self.start.get_value())
        end_value = Decimal("%.2f" % self.end.get_value())
        option = self.mode.get_selected_data()

        start, end = option().get_interval(start_value, end_value)
        return NumberIntervalQueryState(filter=self, start=start, end=end)

    def set_state(self, start, end):
        self.start.set_value(start)
        self.end.set_value(end)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = ''
        option = self.mode.get_selected_data()
        if option is not None:
            desc += option.name
            if option.numbers > 0:
                start = self.start.get_value_as_int()
                if option.numbers == 1:
                    desc += ' %d' % start
                elif option.numbers == 2:
                    end = self.end.get_value_as_int()
                    desc += ' %d %s %d' % (start, self.and_label.get_text(), end,)
        if desc:
            return '%s %s' % (self.get_title_label().get_text(), desc)

    #
    #   Public API
    #

    def add_option(self, option_type, position=-2):
        """
        Adds a date option
        @param option_type: option to add
        @type option_type: a L{NumberSearchOption} subclass
        """
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option


#
# Other UI pieces
#

class SearchFilterButton(gtk.Button):
    def __init__(self, label=None, stock=None, use_underline=True):
        gtk.Button.__init__(self, label, stock, use_underline)
        self.set_icon_size(gtk.ICON_SIZE_MENU)
        self.set_relief(gtk.RELIEF_NONE)
        if label != stock and label:
            self._set_label(label)

    def _set_label(self, label):
        self.get_children()[0].get_child().get_children()[1].set_label(label)

    def set_label_visible(self, visible):
        self.get_children()[0].get_child().get_children()[1].hide()

    def set_icon_size(self, icon_size):
        icon = self.get_children()[0].get_child().get_children()[0]
        icon.set_property('icon-size', icon_size)


class SearchResults(ObjectList):
    def __init__(self, columns):
        ObjectList.__init__(self, columns)


class SearchContainer(gtk.VBox):
    """
    A search container is a widget which consists of:
    - search entry (w/ a label) (L{StringSearchFilter})
    - search button
    - objectlist result (L{SearchResult})
    - a query executer (L{kiwi.db.query.QueryExecuter})

    Additionally you can add a number of search filters to the SearchContainer.
    You can chose if you want to add the filter in the top-left corner
    of bottom, see L{SearchFilterPosition}
    """
    __gtype_name__ = 'SearchContainer'
    filter_label = gobject.property(type=str)
    results_class = SearchResults
    gsignal("search-completed", object, object)

    def __init__(self, columns=None, chars=25):
        """
        Create a new SearchContainer object.
        @param columns: a list of L{kiwi.ui.objectlist.Column}
        @param chars: maximum number of chars used by the search entry
        """
        gtk.VBox.__init__(self)
        self._columns = columns
        self._search_filters = []
        self._query_executer = None
        self._auto_search = True
        self._summary_label = None

        search_filter = StringSearchFilter(_('Search:'), chars=chars)
        search_filter.connect('changed', self._on_search_filter__changed)
        self._search_filters.append(search_filter)
        self._primary_filter = search_filter

        self._create_ui()


    #
    # GObject
    #

    def do_set_property(self, pspec, value):
        if pspec.name == 'filter-label':
            self._primary_filter.set_label(value)
        else:
            raise AssertionError(pspec.name)

    def do_get_property(self, pspec):
        if pspec.name == 'filter-label':
            return self._primary_filter.get_label()
        else:
            raise AssertionError(pspec.name)

    #
    # GtkContainer
    #

    def do_set_child_property(self, child, property_id, value, pspec):
        if pspec.name == 'filter-position':
            if value == 'top':
                pos = SearchFilterPosition.TOP
            elif value == 'bottom':
                pos = SearchFilterPosition.BOTTOM
            else:
                raise Exception(pos)
            self.set_filter_position(child, pos)
        else:
            raise AssertionError(pspec.name)

    def do_get_child_property(self, child, property_id, pspec):
        if pspec.name == 'filter-position':
            return self.get_filter_position(child)
        else:
            raise AssertionError(pspec.name)


    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """
        Adds a search filter
        @param search_filter: the search filter
        @param postition: a L{SearchFilterPosition} enum
        @param columns:
        @param callback:
        """

        if not isinstance(search_filter, SearchFilter):
            raise TypeError("search_filter must be a SearchFilter subclass, "
                            "not %r" % (search_filter,))

        if columns and callback:
            raise TypeError("Cannot specify both column and callback")

        executer = self.get_query_executer()
        if executer:
            if columns:
                executer.set_filter_columns(search_filter, columns)
            if callback:
                if not callable(callback):
                    raise TypeError("callback must be callable")
                executer.add_filter_query_callback(search_filter, callback)
        else:
            if columns or callback:
                raise TypeError(
                    "You need to set an executor before calling set_filters "
                    "with columns or callback set")

        assert not search_filter.parent
        self.set_filter_position(search_filter, position)
        search_filter.connect('changed', self._on_search_filter__changed)
        search_filter.connect('removed', self._on_search_filter__remove)
        self._search_filters.append(search_filter)

    def remove_filter(self, filter):
        self.filters_box.remove(filter)
        self._search_filters.remove(filter)
        filter.destroy()

        if self._auto_search:
            self.search()

    def get_search_filters(self):
        return self._search_filters

    def get_search_filter_by_label(self, label):
        for search_filter in self._search_filters:
            if search_filter.label == label:
                return search_filter

    def set_filter_position(self, search_filter, position):
        """
        Set the the filter position.
        @param search_filter:
        @param position:
        """
        if search_filter.parent:
            search_filter.parent.remove(search_filter)

        if position == SearchFilterPosition.TOP:
            self.hbox.pack_start(search_filter, False, False)
            self.hbox.reorder_child(search_filter, 0)
        elif position == SearchFilterPosition.BOTTOM:
            self.filters_box.pack_start(search_filter, False, False)
        search_filter.show()

    def get_filter_position(self, search_filter):
        """
        Get filter by position.
        @param search_filter:
        """
        if search_filter.parent == self.hbox:
            return SearchFilterPosition.TOP
        elif search_filter.parent == self:
            return SearchFilterPosition.BOTTOM
        else:
            raise AssertionError(search_filter)

    def set_query_executer(self, querty_executer):
        """
        Ties a QueryExecuter instance to the SearchContainer class
        @param querty_executer: a querty executer
        @type querty_executer: a L{QueryExecuter} subclass
        """
        if not isinstance(querty_executer, QueryExecuter):
            raise TypeError("querty_executer must be a QueryExecuter instance")

        self._query_executer = querty_executer

    def get_query_executer(self):
        """
        Fetchs the QueryExecuter for the SearchContainer
        @returns: a querty executer
        @rtype: a L{QueryExecuter} subclass
        """
        return self._query_executer

    def get_primary_filter(self):
        """
        Fetches the primary filter for the SearchContainer.
        The primary filter is the filter attached to the standard entry
        normally used to do free text searching
        @returns: the primary filter
        """
        return self._primary_filter

    def search(self):
        """
        Starts a search.
        Fetches the states of all filters and send it to a query executer and
        finally puts the result in the result class
        """
        if not self._query_executer:
            raise ValueError("A query executer needs to be set at this point")
        states = [(sf.get_state()) for sf in self._search_filters]
        results = self._query_executer.search(states)
        self.add_results(results)
        self.emit("search-completed", self.results, states)
        if self._summary_label:
            self._summary_label.update_total()

    def set_auto_search(self, auto_search):
        """
        Enables/Disables auto search which means that the search result box
        is automatically populated when a filter changes
        @param auto_search: True to enable, False to disable
        """
        self._auto_search = auto_search

    def set_text_field_columns(self, columns):
        if self._primary_filter is None:
            raise ValueError("The primary filter is disabled")

        if not self._query_executer:
            raise ValueError("A query executer needs to be set at this point")

        self._query_executer.set_filter_columns(self._primary_filter, columns)

    def disable_search_entry(self):
        """
        Disables the search entry
        """
        self.search_entry.hide()
        self._primary_filter.hide()
        self._search_filters.remove(self._primary_filter)
        self._primary_filter = None

    def set_summary_label(self, column, label='Total:', format='%s',
                          parent=None):
        """
        Adds a summary label to the result set
        @param column: the column to sum from
        @param label: the label to use, defaults to 'Total:'
        @param format: the format, defaults to '%%s', must include '%%s'
        @param parent: the parent widget a label should be added to or
           None if it should be added to the SearchContainer
        """
        if not '%s' in format:
            raise ValueError("format must contain %s")

        try:
            self.results.get_column_by_name(column)
        except LookupError:
            raise ValueError("%s is not a valid column" % (column,))

        if not parent:
            parent = self
        elif not isinstance(parent, gtk.Box):
            raise TypeError("parent %r must be a GtkBox subclass" % (
                parent))

        if self._summary_label:
            self._summary_label.parent.remove(self._summary_label)
        self._summary_label = SummaryLabel(klist=self.results,
                                           column=column,
                                           label=label,
                                           value_format=format)
        parent.pack_end(self._summary_label, False, False)
        self._summary_label.show()

    def enable_advanced_search(self):
        self._create_advanced_search()

    def add_results(self, results):
        self.results.clear()
        self.results.extend(results)

    def get_filter_states(self):
        dict_state = {}
        for search_filter in self._search_filters:
            dict_state[search_filter.label] = data = {}
            state = search_filter.get_state()
            if isinstance(state, DateQueryState):
                data['start'] = state.date
            elif isinstance(state, DateIntervalQueryState):
                data['start'] = state.start
                data['end'] = state.end
            elif isinstance(state, NumberQueryState):
                data['value'] = state.value
                if hasattr(state, 'value_id'):
                    data['value_id'] = state.value_id
            elif isinstance(state, NumberIntervalQueryState):
                data['start'] = state.start
                data['end'] = state.end
            elif isinstance(state, StringQueryState):
                data['text'] = state.text
                data['mode'] = state.mode
            else:
                raise NotImplementedError(state)
        return dict_state

    def set_filter_states(self, dict_state):
        for label, filter_state in dict_state.items():
            search_filter = self.get_search_filter_by_label(label)
            if search_filter is None:
                continue
            search_filter.set_state(**filter_state)


    #
    # Callbacks
    #

    def _on_search_button__clicked(self, button):
        self.search()

    def _on_search_entry__activate(self, button):
        self.search()

    def _on_search_filter__remove(self, filter):
        self.remove_filter(filter)

    def _on_search_filter__changed(self, search_filter):
        if self._auto_search:
            self.search()

    #
    # Private
    #

    def _create_ui(self):
        self._create_basic_search()

        self.results = self.results_class(self._columns)
        self.pack_end(self.results, True, True, 0)
        self.results.show()

    def _create_basic_search(self):
        filters_box = gtk.VBox()
        filters_box.show()
        self.pack_start(filters_box, expand=False)

        hbox = gtk.HBox()
        hbox.set_border_width(3)
        filters_box.pack_start(hbox, False, False)
        hbox.show()
        self.hbox = hbox

        widget = self._primary_filter
        self.hbox.pack_start(widget, False, False)
        widget.show()

        self.search_entry = self._primary_filter.entry
        self.search_entry.connect('activate',
                                  self._on_search_entry__activate)

        self.search_button = SearchFilterButton(stock=gtk.STOCK_FIND)
        self.search_button.connect('clicked', self._on_search_button__clicked)
        hbox.pack_start(self.search_button, False, False)
        self.search_button.show()

        self.filters_box = filters_box

    def _create_advanced_search(self):
        self.label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.combo_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        add = SearchFilterButton(label=_('Filter'), stock=gtk.STOCK_ADD)
        add.connect('clicked', self._on_add_field_clicked)
        add.show()
        self.hbox.pack_end(add, False, False, 0)

        self.add_filter_button = add

        self.menu = gtk.Menu()
        for column in self._columns:
            if not isinstance(column, SearchColumn):
                continue

            if column.data_type not in (datetime.date, Decimal, int, currency,
                                        str):
                continue

            title = column.long_title or column.title

            menu_item = gtk.MenuItem(title)
            menu_item.set_data('column', column)
            menu_item.show()
            menu_item.connect('activate', self._on_menu_item_activate)
            self.menu.append(menu_item)

        if not len(self.menu):
            self.add_filter_button.hide()

    def _position_filter_menu(self, data):
        alloc = self.add_filter_button.get_allocation()
        x, y = self.add_filter_button.window.get_origin()

        return (x + alloc.x, y + alloc.y + alloc.height, True)

    def _on_add_field_clicked(self, button):
        self.menu.popup(None, None, self._position_filter_menu, 0, 0L)

    def _on_menu_item_activate(self, item):
        column = item.get_data('column')

        if column is None:
            return

        title = (column.long_title or column.title) + ':'

        if column.data_type == datetime.date:
            filter = DateSearchFilter(title)
            if column.valid_values:
                filter.clear_options()
                filter.add_custom_options()
                for opt in column.valid_values:
                    filter.add_option(opt)
                filter.select(column.valid_values[0])

        elif (column.data_type == Decimal or
              column.data_type == int or
              column.data_type == currency):
            filter = NumberSearchFilter(title)
            if column.data_type != int:
                filter.set_digits(2)
        elif column.data_type == str:
            if column.valid_values:
                filter = ComboSearchFilter(title, column.valid_values)
            else:
                filter = StringSearchFilter(title)
                filter.enable_advaced()
        else:
            # TODO: Boolean
            raise NotImplementedError

        filter.set_removable()
        attr = column.search_attribute or column.attribute
        self.add_filter(filter, columns=[attr])

        label = filter.get_title_label()
        label.set_alignment(1.0, 0.5)
        self.label_group.add_widget(label)
        combo = filter.get_mode_combo()
        if combo:
            self.combo_group.add_widget(combo)


SearchContainer.install_child_property(
    1, ('filter-position', str,
        'Search Filter Position',
        'The search filter position in the container',
        '', gobject.PARAM_READWRITE))


class SearchSlaveDelegate(SlaveDelegate):
    def __init__(self, columns):
        """
        Create a new SearchSlaveDelegate object.
        @ivar results: the results list of the container
        @ivar search: the L{SearchContainer}
        """
        self.search = SearchContainer(columns)
        SlaveDelegate.__init__(self, toplevel=self.search)
        self.results = self.search.results
        self.search.show()


    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """
        See L{SearchSlaveDelegate.add_filter}
        """
        self.search.add_filter(search_filter, position, columns, callback)

    def set_query_executer(self, querty_executer):
        """
        See L{SearchSlaveDelegate.set_query_executer}
        """
        self.search.set_query_executer(querty_executer)

    def set_text_field_columns(self, columns):
        """
        See L{SearchSlaveDelegate.set_text_field_columns}
        """
        self.search.set_text_field_columns(columns)

    def get_primary_filter(self):
        """
        Fetches the primary filter of the SearchSlaveDelegate
        @returns: primary filter
        """
        return self.search.get_primary_filter()

    def focus_search_entry(self):
        """
        Grabs the focus of the search entry
        """
        self.search.search_entry.grab_focus()

    def refresh(self):
        """
        Triggers a search again with the currently selected inputs
        """
        self.search.search()

    def clear(self):
        """
        Clears the result list
        """
        self.search.results.clear()

    def disable_search_entry(self):
        """
        Disables the search entry
        """
        self.search.disable_search_entry()

    def set_summary_label(self, column, label='Total:', format='%s',
                          parent=None):
        """
        See L{SearchContainer.set_summary_label}
        """
        self.search.set_summary_label(column, label, format, parent)

    def enable_advanced_search(self):
        """
        See L{SearchContainer.enable_advanced_search}
        """
        self.search.enable_advanced_search()

    def get_search_filters(self):
        return self.search.get_search_filters()

    #
    # Overridable
    #

    def get_columns(self):
        """
        This needs to be implemented in a subclass
        @returns: columns
        @rtype: list of L{kiwi.ui.objectlist.Column}
        """
        raise NotImplementedError
