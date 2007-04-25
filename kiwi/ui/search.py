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
import gettext

import gobject
import gtk

from kiwi.component import implements
from kiwi.db.query import (NumberQueryState, StringQueryState,
                           DateQueryState, DateIntervalQueryState,
                           QueryExecuter)
from kiwi.enums import SearchFilterPosition
from kiwi.interfaces import ISearchFilter
from kiwi.python import enum
from kiwi.ui.dateentry import DateEntry
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.utils import gsignal

_ = lambda m: gettext.dgettext('kiwi', m)

class DateSearchOption(object):
    """
    Base class for Date search options
    A date search option is an interval of dates
    @cvar name: name of the search option
    """
    name = None

    def get_interval(self):
        """
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
        today = datetime.date.today()
        return today, today


class Yesterday(DateSearchOption):
    name = _('Yesterday')

    def get_interval(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        return yesterday, yesterday


class LastWeek(DateSearchOption):
    name = _('Last week')

    def get_interval(self):
        today = datetime.date.today()
        return (today - datetime.timedelta(days=7), today)


class LastMonth(DateSearchOption):
    name = _('Last month')

    def get_interval(self):
        today = datetime.date.today()
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
        return start_date, datetime.date.today()


class DateSearchFilter(gobject.GObject):
    """
    A filter which helps you to search by a date interval.
    Can be customized through add_option.
    """
    gsignal('changed')
    implements(ISearchFilter)
    class Type(enum):
        (USER_DAY,
         USER_INTERVAL) = range(100, 102)

    def __init__(self, name):
        """
        @param name: name of the search filter
        """
        gobject.GObject.__init__(self)
        self._options = {}
        hbox = gtk.HBox()
        hbox.set_border_width(6)
        label = gtk.Label(name)
        hbox.pack_start(label, False, False)
        label.show()

        self.mode = ProxyComboBox()
        self.mode.connect(
            'content-changed',
            self._on_mode__content_changed)
        hbox.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.from_label = gtk.Label(_("From:"))
        hbox.pack_start(self.from_label, False, False)
        self.from_label.show()

        self.start_date = DateEntry()
        self._start_changed_id = self.start_date.connect(
            'changed', self._on_start_date__changed)
        hbox.pack_start(self.start_date, False, False, 6)
        self.start_date.show()

        self.to_label = gtk.Label(_("To:"))
        hbox.pack_start(self.to_label, False, False)
        self.to_label.show()

        self.end_date = DateEntry()
        self._end_changed_id = self.end_date.connect(
            'changed', self._on_end_date__changed)
        hbox.pack_start(self.end_date, False, False, 6)
        self.end_date.show()

        self.hbox = hbox

        self.mode.prefill([
            (_('Custom day'), DateSearchFilter.Type.USER_DAY),
            (_('Custom interval'), DateSearchFilter.Type.USER_INTERVAL),
            ])

        for option in (Any, Today, Yesterday, LastWeek, LastMonth):
            self.add_option(option)

        self.mode.select_item_by_position(0)

    def add_option(self, option_type):
        """
        Adds a date option
        @param option_type: option to add
        @type option_type: a L{DateSearchOption} subclass
        """
        option = option_type()
        num = len(self.mode)-2
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option

    def get_widget(self):
        return self.hbox

    def get_state(self):
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if start == end:
            return DateQueryState(filter=self, date=start)
        return DateIntervalQueryState(filter=self, start=start, end=end)

    def select(self, data):
        """
        selects an item in the combo
        @param data: what to select
        """
        self.mode.select(data)

    #
    # Private
    #

    def _update_dates(self):
        # This is called when we change mode
        date_type = self.mode.get_selected_data()

        # If we switch to a user selectable day, make sure that
        # both dates are set to the same day
        if date_type == DateSearchFilter.Type.USER_DAY:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            if start != end:
                self.end_date.set_date(self.start_date.get_date())
        # And for user interval, do the opposite, make sure
        # that start and end are different
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            if start and end and start == end:
                self.end_date.set_date(start + datetime.timedelta(days=1))
        # Finally for pre-defined ones let the DateSearchOption decide what the
        # values are going to be, these dates are not user editable so
        # we don't need to do any checking.
        else:
            option = self._options.get(date_type)
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

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, mode):
        self._update_dates()
        self._update_sensitivity()
        self.emit('changed')

    def _on_start_date__changed(self, start_date):
        date_type = self.mode.get_selected_data()
        start = start_date.get_date()
        # For user days, just make sure that the date entries
        # always are in sync
        if date_type == DateSearchFilter.Type.USER_DAY:
            self._internal_set_end_date(start)
        # Make sure that we cannot select a start date after
        # the end date, be nice and increase the end date if
        # the start date happen to be the same
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            end = self.end_date.get_date()
            if not start or not end:
                return
            if start >= end:
                self._internal_set_end_date(start + datetime.timedelta(days=1))

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
            if not start or not end:
                return
            if end <= start:
                self._internal_set_start_date(end - datetime.timedelta(days=1))

class ComboSearchFilter(gobject.GObject):
    """
    - a label
    - a combo with a set of predefined item to select from
    """
    gsignal('changed')
    implements(ISearchFilter)
    def __init__(self, name, values):
        """
        @param name: name of the search filter
        @param values: items to put in the combo, see
          L{kiwi.ui.widgets.combo.ProxyComboBox.prefill}
        """
        gobject.GObject.__init__(self)
        hbox = gtk.HBox()
        label = gtk.Label(name)
        hbox.pack_start(label, False, False)
        label.show()

        self.combo = ProxyComboBox()
        self.combo.prefill(values)
        self.combo.connect(
            'content-changed',
            self._on_combo__content_changed)
        hbox.pack_start(self.combo, False, False, 6)
        self.combo.show()

        self.hbox = hbox

    def select(self, data):
        """
        selects an item in the combo
        @param data: what to select
        """
        self.combo.select(data)

    def get_widget(self):
        return self.hbox

    def get_state(self):
        return NumberQueryState(filter=self,
                                value=self.combo.get_selected_data())

    #
    # Callbacks
    #

    def _on_combo__content_changed(self, mode):
        self.emit('changed')

class StringSearchFilter(gobject.GObject):
    """
    - a label
    - an entry
    @ivar entry: the entry
    @ivar label: the label
    """
    gsignal('changed')
    implements(ISearchFilter)
    def __init__(self, name, chars=0):
        """
        @param name: name of the search filter
        @param chars: maximum number of chars used by the search entry
        """
        gobject.GObject.__init__(self)
        hbox = gtk.HBox()
        self.label = gtk.Label(name)
        hbox.pack_start(self.label, False, False)
        self.label.show()

        self.entry = gtk.Entry()
        if chars:
            self.entry.set_width_chars(chars)
        hbox.pack_start(self.entry, False, False, 6)
        self.entry.show()

        self.hbox = hbox

    def get_widget(self):
        return self.hbox

    def get_state(self):
        return StringQueryState(filter=self,
                                text=self.entry.get_text())

    def set_label(self, label):
        self.label.set_text(label)


#
# Other UI pieces
#

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
    def __init__(self, columns=None, chars=25):
        """
        @param columns: a list of L{kiwi.ui.objectlist.Column}
        @param chars: maximum number of chars used by the search entry
        """
        gtk.VBox.__init__(self)
        self._columns = columns
        self._search_filters = []
        self._query_executer = None
        self._auto_search = True

        search_filter = StringSearchFilter(_('Search:'), chars=chars)
        search_filter.connect('changed', self._on_search_filter__changed)
        self._search_filters.append(search_filter)
        self._primary_filter = search_filter

        self._create_ui()


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

        if not ISearchFilter.providedBy(search_filter):
            raise TypeError("search_filter must implement ISearchFilter")

        if columns and callback:
            raise TypeError("Cannot specify both column and callback")

        executer = self.get_query_executer()
        if not executer:
            raise ValueError

        if columns:
            executer.set_filter_columns(search_filter, columns)
        if callback:
            if not callable(callback):
                raise TypeError("callback must be callable")
            executer.add_filter_query_callback(search_filter, callback)

        widget = search_filter.get_widget()
        assert not widget.parent
        if position == SearchFilterPosition.TOP:
            self.hbox.pack_start(widget, False, False)
            self.hbox.reorder_child(widget, 0)
        elif position == SearchFilterPosition.BOTTOM:
            self.pack_start(widget, False, False)
        widget.show()

        search_filter.connect('changed', self._on_search_filter__changed)
        self._search_filters.append(search_filter)

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
        self.results.clear()
        self.results.extend(results)

    def set_auto_search(self, auto_search):
        """
        Enables/Disables auto search which means that the search result box
        is automatically populated when a filter changes
        @param auto_search: True to enable, False to disable
        """
        self._auto_search = auto_search

    def set_text_field_columns(self, columns):
        """
        @param columns:
        """
        if not self._query_executer:
            raise ValueError("A query executer needs to be set at this point")

        self._query_executer.set_filter_columns(self._primary_filter, columns)

    #
    # Callbacks
    #

    def _on_search_button__clicked(self, button):
        self.search()

    def _on_search_entry__activate(self, button):
        self.search()

    def _on_search_filter__changed(self, search_filter):
        if self._auto_search:
            self.search()

    #
    # Private
    #

    def _create_ui(self):
        hbox = gtk.HBox()
        hbox.set_border_width(6)
        self.pack_start(hbox, False, False)
        hbox.show()
        self.hbox = hbox

        widget = self._primary_filter.get_widget()
        self.hbox.pack_start(widget, False, False)
        widget.show()

        self.search_entry = self._primary_filter.entry
        self.search_entry.connect('activate',
                                  self._on_search_entry__activate)
        button = gtk.Button(stock=gtk.STOCK_FIND)
        button.connect('clicked', self._on_search_button__clicked)
        hbox.pack_start(button, False, False)
        button.show()

        self.results = SearchResults(self._columns)
        self.pack_end(self.results, True, True, 6)
        self.results.show()

class SearchSlaveDelegate(SlaveDelegate):
    """
    @ivar results: the results list of the container
    @ivar search: the L{SearchContainer}
    """
    def __init__(self, columns):
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
