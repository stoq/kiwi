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


class DateSearchFilter(object):
    """
    A filter which helps you to search by a date interval.
    Can be customized through add_option.
    """
    implements(ISearchFilter)
    class Type(enum):
        (CUSTOM_DAY,
         CUSTOM_INTERVAL) = range(100, 102)

    def __init__(self, name):
        """
        @param name: name of the search filter
        """
        self._options = {}
        hbox = gtk.HBox()
        hbox.set_border_width(6)
        label = gtk.Label(name)
        hbox.pack_start(label, False, False)
        label.show()

        self.mode = ProxyComboBox()
        self.mode.connect('content-changed',
                          self._on_mode__content_changed)
        hbox.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.from_label = gtk.Label(_("From:"))
        hbox.pack_start(self.from_label, False, False)
        self.from_label.show()

        self.start_date = DateEntry()
        self.start_date.connect('changed',
                                self._on_start_date__changed)
        hbox.pack_start(self.start_date, False, False, 6)
        self.start_date.show()

        self.to_label = gtk.Label(_("To:"))
        hbox.pack_start(self.to_label, False, False)
        self.to_label.show()

        self.end_date = DateEntry()
        hbox.pack_start(self.end_date, False, False, 6)
        self.end_date.show()

        self.hbox = hbox

        self.mode.prefill([
            (_('Custom day'), DateSearchFilter.Type.CUSTOM_DAY),
            (_('Custom interval'), DateSearchFilter.Type.CUSTOM_INTERVAL),
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
        self.mode.insert_item(num, option.name, num)
        self._options[num] = option

    def get_widget(self):
        return self.hbox

    def get_state(self):
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if start == end:
            return DateQueryState(filter=self, date=start)
        return DateIntervalQueryState(filter=self, start=start, end=end)

    #
    # Private
    #

    def _update_dates(self):
        date_type = self.mode.get_selected_data()
        if date_type not in [DateSearchFilter.Type.CUSTOM_DAY,
                             DateSearchFilter.Type.CUSTOM_INTERVAL]:
            option = self._options.get(date_type)
            start_date, end_date = option.get_interval()
            self.start_date.set_date(start_date)
            self.end_date.set_date(end_date)

    def _update_sensitivity(self):
        date_type = self.mode.get_selected_data()
        enabled = date_type == DateSearchFilter.Type.CUSTOM_INTERVAL
        self.to_label.set_sensitive(enabled)
        self.end_date.set_sensitive(enabled)

        enabled = (date_type == DateSearchFilter.Type.CUSTOM_INTERVAL or
                   date_type == DateSearchFilter.Type.CUSTOM_DAY)
        self.from_label.set_sensitive(enabled)
        self.start_date.set_sensitive(enabled)

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, mode):
        self._update_dates()
        self._update_sensitivity()

    def _on_start_date__changed(self, start_date):
        date_type = self.mode.get_selected_data()
        if date_type == DateSearchFilter.Type.CUSTOM_DAY:
            self.start_date.set_date(start_date.get_date())
            self.end_date.set_date(start_date.get_date())


class ComboSearchFilter(object):
    """
    - a label
    - a combo with a set of predefined item to select from
    """
    implements(ISearchFilter)
    def __init__(self, name, values):
        """
        @param name: name of the search filter
        @param values: items to put in the combo, see
          L{kiwi.ui.widgets.combo.ProxyComboBox.prefill}
        """
        hbox = gtk.HBox()
        label = gtk.Label(name)
        hbox.pack_start(label, False, False)
        label.show()

        self.combo = ProxyComboBox()
        self.combo.prefill(values)
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


class StringSearchFilter(object):
    """
    - a label
    - an entry
    @ivar entry: the entry
    @ivar label: the label
    """
    implements(ISearchFilter)
    def __init__(self, name, chars=0):
        """
        @param name: name of the search filter
        @param chars: maximum number of chars used by the search entry
        """
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
        self._querty_executer = None

        search_filter = StringSearchFilter(_('Search:'), chars=chars)
        self._search_filters.append(search_filter)
        self._primary_filter = search_filter

        self._create_ui()


    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM):
        """
        Adds a search filter
        @param search_filter: the search filter
        @param postition: a L{SearchFilterPosition} enum
        """
        if not ISearchFilter.providedBy(search_filter):
            raise TypeError("search_filter must implement ISearchFilter")

        widget = search_filter.get_widget()
        assert not widget.parent
        if position == SearchFilterPosition.TOP:
            self.hbox.pack_start(widget, False, False)
            self.hbox.reorder_child(widget, 0)
        elif position == SearchFilterPosition.BOTTOM:
            self.pack_start(widget, False, False)
        widget.show()

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

    #
    # Callbacks
    #

    def _on_search_entry_activate(self, entry):
        self.search()

    def _on_search_button__clicked(self, button):
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
        self.search_entry.connect('activate', self._on_search_entry_activate)

        button = gtk.Button(stock=gtk.STOCK_FIND)
        button.connect('clicked', self._on_search_button__clicked)
        hbox.pack_start(button, False, False)
        button.show()

        self.results = SearchResults(self._columns)
        self.pack_end(self.results, True, True, 6)
        self.results.show()

class SearchSlaveDelegate(SlaveDelegate):
    def __init__(self, columns):
        self.search = SearchContainer(columns)
        SlaveDelegate.__init__(self, toplevel=self.search)

    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM):
        """
        Adds a search filter
        @param search_filter: the search filter
        @param postition: a L{SearchFilterPosition} enum
        """
        self.search.add_filter(search_filter, position)

    def set_query_executer(self, querty_executer):
        """
        Ties a QueryExecuter instance to the SearchSlaveDelegate class
        @param querty_executer: a querty executer
        @type querty_executer: a L{QueryExecuter} subclass
        """
        if not isinstance(querty_executer, QueryExecuter):
            raise TypeError("querty_executer must be a QueryExecuter instance")

        self.search.set_query_executer(querty_executer)


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
