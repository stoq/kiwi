##
## Copyright (C) 2007 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s):    Ali Afshar              <aafshar@gmail.com>
##               Johan Dahlin            <jdahlin@async.com.br>
##

"""
SQLAlchemy integration for Kiwi
"""

from sqlalchemy import and_, or_, not_

from kiwi.db.query import NumberQueryState, StringQueryState, \
     DateQueryState, DateIntervalQueryState, QueryExecuter, \
     NumberIntervalQueryState
from kiwi.interfaces import ISearchFilter


class SQLAlchemyQueryExecuter(QueryExecuter):
    def __init__(self, session):
        QueryExecuter.__init__(self)
        self.session = session
        self.table = None
        self._query_callbacks = []
        self._filter_query_callbacks = {}
        self._query = self._default_query
        self._full_text_indexes = {}

    #
    # Public API
    #

    def set_table(self, table):
        """
        Sets the SQLObject table/object for this executer
        @param table: a SQLObject subclass
        """
        self.table = table

    def add_query_callback(self, callback):
        """
        Adds a generic query callback

        @param callback: a callable
        """
        if not callable(callback):
            raise TypeError
        self._query_callbacks.append(callback)

    def add_filter_query_callback(self, search_filter, callback):
        """
        Adds a query callback for the filter search_filter

        @param search_filter: a search filter
        @param callback: a callable
        """
        if not ISearchFilter.providedBy(search_filter):
            raise TypeError
        if not callable(callback):
            raise TypeError
        l = self._filter_query_callbacks.setdefault(search_filter, [])
        l.append(callback)

    def set_query(self, callback):
        """
        Overrides the default query mechanism.
        @param callback: a callable which till take two arguments:
          (query, connection)
        """
        if callback is None:
            callback = self._default_query
        elif not callable(callback):
            raise TypeError

        self._query = callback

    #
    # QueryBuilder
    #

    def search(self, states):
        """
        Execute a search.
        @param states:
        """
        if self.table is None:
            raise ValueError("table cannot be None")
        table = self.table
        queries = []
        for state in states:
            search_filter = state.filter
            assert state.filter

            # Column query
            if search_filter in self._columns:
                query = self._construct_state_query(
                    table, state, self._columns[search_filter])
                if query:
                    queries.append(query)
            # Custom per filter/state query.
            elif search_filter in self._filter_query_callbacks:
                for callback in self._filter_query_callbacks[search_filter]:
                    query = callback(state)
                    if query:
                        queries.append(query)
            else:
                if (self._query == self._default_query and
                    not self._query_callbacks):
                    raise ValueError(
                        "You need to add a search column or a query callback "
                        "for filter %s" % (search_filter))

        for callback in self._query_callbacks:
            query = callback(states)
            if query:
                queries.append(query)

        if queries:
            query = and_(*queries)
        else:
            query = None
        result = self._query(query)
        return result

    #
    # Private
    #

    def _default_query(self, query):
        return self.session.query(self.table).select(query)

    def _construct_state_query(self, table, state, columns):
        queries = []
        for column in columns:
            query = None
            table_field = getattr(table.c, column)
            if isinstance(state, NumberQueryState):
                query = self._parse_number_state(state, table_field)
            elif isinstance(state, NumberIntervalQueryState):
                query = self._parse_number_interval_state(state, table_field)
            elif isinstance(state, StringQueryState):
                query = self._parse_string_state(state, table_field)
            elif isinstance(state, DateQueryState):
                query = self._parse_date_state(state, table_field)
            elif isinstance(state, DateIntervalQueryState):
                query = self._parse_date_interval_state(state, table_field)
            else:
                raise NotImplementedError(state.__class__.__name__)

            if query:
                queries.append(query)

        if queries:
            return or_(*queries)

    def _parse_number_state(self, state, table_field):
        if state.value is not None:
            return table_field == state.value

    def _parse_number_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(table_field <= state.end)
        if queries:
            return and_(*queries)

    def _parse_string_state(self, state, table_field):
        if state.text is not None:
            text = '%%%s%%' % state.text.lower()
            retval = table_field.like(text)
        if state.mode == StringQueryState.NOT_CONTAINS:
            retval = not_(retval)

        return retval

    def _parse_date_state(self, state, table_field):
        if state.date:
            return table_field == state.date

    def _parse_date_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(table_field <= state.end)
        if queries:
            return and_(*queries)
