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
## Author(s):    Ali Afshar            <aafshar@gmail.com>
##               Johan Dahlin          <jdahlin@async.com.br>
##

"""
Storm integration for Kiwi
"""

from storm.expr import And, Or, Like, Not

from kiwi.db.query import NumberQueryState, StringQueryState, \
     DateQueryState, DateIntervalQueryState, QueryExecuter, \
     NumberIntervalQueryState


class StormQueryExecuter(QueryExecuter):
    """Execute queries from a storm database"""

    def __init__(self, store=None):
        QueryExecuter.__init__(self)
        self.store = store
        self.table = None

    def search(self, states):
        """
        Build and execute a query for the search states
        """
        queries = []
        for state in states:
            search_filter = state.filter
            assert state.filter
            if search_filter in self._columns:
                query = self._construct_state_query(
                    self.table, state, self._columns[search_filter])
                if query:
                    queries.append(query)
        # Storm will unpack those values.
        return self.store.find(self.table, *queries)

    def set_table(self, table):
        """
        Sets the Storm table/object for this executer
        @param table: a Storm table class
        """
        self.table = table

    # Basically stolen from sqlobject integration
    def _construct_state_query(self, table, state, columns):
        queries = []
        for column in columns:
            query = None
            table_field = getattr(table, column)
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
            return Or(*queries)

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
            return And(*queries)

    def _parse_string_state(self, state, table_field):
        if not state.text:
            return
        text = '%%%s%%' % state.text.lower()
        retval = Like(table_field, text)
        if state.mode == StringQueryState.NOT_CONTAINS:
            retval = Not(retval)

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
            return And(*queries)

