# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

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
## Author(s):    Johan Dahlin            <jdahlin@async.com.br>
##

"""
SQLObject integration for Kiwi
"""

from sqlobject.sqlbuilder import func, AND, OR, LIKE

from kiwi.db.query import (NumberQueryState, StringQueryState,
                           DateQueryState, DateIntervalQueryState,
                           QueryExecuter)
from kiwi.interfaces import ISearchFilter

class SQLObjectQueryExecuter(QueryExecuter):
    def __init__(self, conn):
        QueryExecuter.__init__(self)
        self.conn = conn
        self.table = None
        self._filter_query_callbacks = {}
        self._query = self._default_query

    #
    # Public API
    #

    def set_table(self, table):
        """
        Sets the SQLObject table/object for this executer
        @param table: a SQLObject subclass
        """
        self.table = table

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
            elif self._query != self._default_query:
                continue
            else:
                raise ValueError(
                    "You need to add a search column or a query callback "
                    "for filter %s" % (search_filter))

        return self._query(AND(*queries), self.conn)

    def _default_query(self, query, conn):
        return self.table.select(query, connection=conn)

    #
    # Private
    #

    def _construct_state_query(self, table, state, columns):
        queries = []
        for column in columns:
            query = None
            table_field = getattr(table.q, column)
            if isinstance(state, NumberQueryState):
                query = self._parse_number_state(state, table_field)
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

        return OR(*queries)

    def _parse_number_state(self, state, table_field):
        if state.value is not None:
            return table_field == state.value

    def _parse_string_state(self, state, table_field):
        if state.text:
            text = '%%%s%%' % state.text.lower()
            return LIKE(func.LOWER(table_field), text)

    def _parse_date_state(self, state, table_field):
        if state.date:
            return func.DATE(table_field) == func.DATE(state.date)

    def _parse_date_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= func.DATE(state.start))
        if state.end:
            queries.append(table_field <= func.DATE(state.end))
        return AND(*queries)
