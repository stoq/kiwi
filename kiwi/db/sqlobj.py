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

from sqlobject.sqlbuilder import func, AND, OR, LIKE, SQLExpression, NOT

from kiwi.db.query import NumberQueryState, StringQueryState, \
     DateQueryState, DateIntervalQueryState, QueryExecuter, \
     NumberIntervalQueryState
from kiwi.interfaces import ISearchFilter

class _FTI(SQLExpression):
    def __init__(self, q):
        self.q = q
    def __sqlrepr__(self, db):
        return self.q

class SQLObjectQueryExecuter(QueryExecuter):
    def __init__(self, conn=None):
        QueryExecuter.__init__(self)
        self.conn = conn
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
        self._having = []
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
            query = AND(*queries)
        else:
            query = None

        having = None
        if self._having:
            having = AND(self._having)

        result = self._query(query, having, self.conn)
        return result.limit(self.get_limit())

    #
    # Private
    #

    def _add_having(self, clause):
        self._having.append(clause)

    def _default_query(self, query, having, conn):
        return self.table.select(query, having=having, connection=conn)

    def _construct_state_query(self, table, state, columns):
        queries = []
        having_queries = []

        for column in columns:
            query = None
            table_field = getattr(table.q, column)

            # If the field has an aggregate function (sum, avg, etc..), then
            # this clause should be in the HAVING part of the query.
            use_having = table_field.hasSQLCall()

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

            if query and use_having:
                having_queries.append(query)
                query = None

            if query:
                queries.append(query)

        if having_queries:
            self._add_having(OR(*having_queries))

        if queries:
            return OR(*queries)

    def _postgres_has_fti_index(self, table_name, column_name):
        # Assume that the PostgreSQL full text index columns are
        # named xxx_fti where xxx is the name of the column
        res = self.conn.queryOne(
            """SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND
                  column_name = %s AND
                  udt_name = 'tsvector';""" % (
            self.conn.sqlrepr(table_name),
            self.conn.sqlrepr(column_name)))
        return bool(res)

    def _check_has_fulltext_index(self, table_name, field_name):
        fullname = table_name + field_name
        if fullname in self._full_text_indexes:
            return self._full_text_indexes[fullname]
        else:
            value = False
            if 'postgres' in self.conn.__class__.__module__:
                value = self._postgres_has_fti_index(table_name,
                                                     field_name + '_fti')
            self._full_text_indexes[fullname] = value
        return value

    def _parse_number_state(self, state, table_field):
        if state.value is not None:
            return table_field == state.value

    def _parse_number_interval_state(self, state, table_field):
        queries = []
        if state.start is not None:
            queries.append(table_field >= state.start)
        if state.end is not None:
            queries.append(table_field <= state.end)
        if queries:
            return AND(*queries)

    def _parse_string_state(self, state, table_field):
        if not state.text:
            return

        if self._check_has_fulltext_index(table_field.tableName,
                                          table_field.fieldName):
            value = state.text.lower()
            # FTI operators:
            #  & = AND
            #  | = OR
            value = value.replace(' ', ' & ')
            retval = _FTI("%s.%s_fti @@ %s::tsquery" % (
                table_field.tableName,
                table_field.fieldName,
                self.conn.sqlrepr(value)))
        else:
            text = '%%%s%%' % state.text.lower()
            retval = LIKE(func.LOWER(table_field), text)

        if state.mode == StringQueryState.NOT_CONTAINS:
            retval = NOT(retval)

        return retval

    def _parse_date_state(self, state, table_field):
        if state.date:
            return func.DATE(table_field) == state.date

    def _parse_date_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(func.DATE(table_field) <= state.end)
        if queries:
            return AND(*queries)
