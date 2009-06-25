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
        Create a new QueryState object.
        @param search_filter: search filter this query state is associated with
        @type search_filter: L{SearchFilter}
        """
        self.filter = search_filter


class NumberQueryState(QueryState):
    """
    Create a new NumberQueryState object.
    @cvar value: number
    """
    def __init__(self, filter, value):
        QueryState.__init__(self, filter)
        self.value = value

    def __repr__(self):
        return '<NumberQueryState value=%r>' % (self.value,)


class NumberIntervalQueryState(QueryState):
    """
    Create a new NumberIntervalQueryState object.
    @cvar start: number
    @cvar end: number
    """
    def __init__(self, filter, start, end):
        QueryState.__init__(self, filter)
        self.start = start
        self.end = end

    def __repr__(self):
        return '<NumberIntervalQueryState start=%r end=%r>' % (self.start, self.end)


class StringQueryState(QueryState):
    """
    Create a new StringQueryState object.
    @cvar text: string
    """
    (CONTAINS,
     NOT_CONTAINS) = range(2)

    def __init__(self, filter, text, mode=CONTAINS):
        QueryState.__init__(self, filter)
        self.mode = mode
        self.text = text

    def __repr__(self):
        return '<StringQueryState text=%r>' % (self.text,)


class DateQueryState(QueryState):
    """
    Create a new DateQueryState object.
    @cvar date: date
    """
    def __init__(self, filter, date):
        QueryState.__init__(self, filter)
        self.date = date

    def __repr__(self):
        return '<DateQueryState date=%r>' % (self.date,)


class DateIntervalQueryState(QueryState):
    """
    Create a new DateIntervalQueryState object.
    @cvar start: start of interval
    @cvar end: end of interval
    """
    def __init__(self, filter, start, end):
        QueryState.__init__(self, filter)
        self.start = start
        self.end = end

    def __repr__(self):
        return '<DateIntervalQueryState start=%r, end=%r>' % (
            self.start, self.end)


class QueryExecuter(object):
    """
    A QueryExecuter is responsible for taking the state (as in QueryState)
    objects from search filters and construct a query.
    How the query is constructed is ORM/DB-layer dependent.

    @cvar default_search_limit: The default search limit.
    """
    default_search_limit = 1000

    def __init__(self):
        self._columns = {}
        self._limit = self.default_search_limit

    #
    # Public API
    #

    def set_filter_columns(self, search_filter, columns):
        if not ISearchFilter.providedBy(search_filter):
            pass
            #raise TypeError("search_filter must implement ISearchFilter")

        assert not search_filter in self._columns
        self._columns[search_filter] = columns

    #
    # Overridable
    #

    def search(self, states):
        """
        Execute a search.
        @param states:
        @type states: list of L{QueryStates}
        @returns: list of objects matching query
        """
        raise NotImplementedError

    def set_limit(self, limit):
        """
        Set the maximum number of result items to return in a search query.
        @param limit:
        """
        self._limit = limit

    def get_limit(self):
        return self._limit
