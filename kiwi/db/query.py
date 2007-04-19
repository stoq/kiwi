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

from kiwi.interfaces import ISearchFilter

#
# Query building
#

class QueryState(object):
    def __init__(self, search_filter):
        """
        @param search_filter: search filter this query state is associated with
        @type search_filter: L{SearchFilter}
        """
        self.filter = search_filter

class NumberQueryState(QueryState):
    """
    @cvar value: number
    """
    def __init__(self, filter, value):
        QueryState.__init__(self, filter)
        self.value = value

class StringQueryState(QueryState):
    """
    @cvar text: string
    """
    def __init__(self, filter, text):
        QueryState.__init__(self, filter)
        self.text = text

class DateQueryState(QueryState):
    """
    @cvar date: date
    """
    def __init__(self, filter, date):
        QueryState.__init__(self, filter)
        self.date = date

class DateIntervalQueryState(QueryState):
    """
    @cvar start: start of interval
    @cvar end: end of interval
    """
    def __init__(self, filter, start, end):
        QueryState.__init__(self, filter)
        self.start = start
        self.end = end

class QueryExecuter(object):
    """
    A QueryExecuter is responsible for taking the state (as in QueryState)
    objects from search filters and construct a query.
    How the query is constructed is ORM/DB-layer dependent
    """
    def __init__(self):
        self._columns = {}

    #
    # Public API
    #

    def set_filter_columns(self, search_filter, columns):
        if not ISearchFilter.providedBy(search_filter):
            raise TypeError("search_filter must implement ISearchFilter")

        assert not search_filter in self._columns
        self._columns[search_filter] = columns

    #
    # Overridable
    #

    def search(self, states):
        """
        @param states:
        @type states: list of L{QueryStates}
        @returns: list of objects matching query
        """
        raise NotImplementedError

