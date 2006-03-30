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
# Author(s): Christian Reis <kiko@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#

"""GtkEntry support for the Kiwi Framework"""

import datetime

import gtk

from kiwi.datatypes import ValidationError, converter, number
from kiwi.decorators import deprecated
from kiwi.python import deprecationwarn
from kiwi.ui.entry import MaskError, KiwiEntry, ENTRY_MODE_TEXT, \
     ENTRY_MODE_DATA
from kiwi.ui.dateentry import DateEntry
from kiwi.ui.proxywidget import ValidatableProxyWidgetMixin
from kiwi.utils import PropertyObject, gsignal, type_register

DATE_MASK_TABLE = {
    '%m': '%2d',
    '%y': '%2d',
    '%d': '%2d',
    '%Y': '%4d',
    '%H': '%2d',
    '%M': '%2d',
    '%S': '%2d',
    '%T': '%2d:%2d:%2d',
    # FIXME: locale specific
    '%r': '%2d:%2d:%2d %2c',
    }

class ProxyEntry(KiwiEntry, ValidatableProxyWidgetMixin):
    """The Kiwi Entry widget has many special features that extend the basic
    gtk entry.

    First of all, as every Kiwi Widget, it implements the Proxy protocol.
    As the users types the entry can interact with the application model
    automatically.
    Kiwi Entry also implements interesting UI additions. If the input data
    does not match the data type of the entry the background nicely fades
    to a light red color. As the background changes an information icon
    appears. When the user passes the mouse over the information icon a
    tooltip is displayed informing the user how to correctly fill the
    entry. When dealing with date and float data-type the information on
    how to fill these entries is displayed according to the current locale.
    """

    __gtype_name__ = 'ProxyEntry'

    def __init__(self, data_type=None):
        self._block_changed = False
        KiwiEntry.__init__(self)
        ValidatableProxyWidgetMixin.__init__(self)
        self.set_property('data-type', data_type)

    # Virtual methods
    gsignal('changed', 'override')
    def do_changed(self):
        """Called when the content of the entry changes.

        Sets an internal variable that stores the last time the user
        changed the entry
        """

        self.chain()

        self._update_current_object(self.get_text())
        self.emit('content-changed')

    def prop_set_data_type(self, data_type):
        data_type = super(ProxyEntry, self).prop_set_data_type(data_type)

        # Numbers should be right aligned
        if data_type and issubclass(data_type, number):
            self.set_property('xalign', 1.0)

        # Apply a mask for the data types, some types like
        # dates has a default mask
        try:
            self.set_mask_for_data_type(data_type)
        except MaskError:
            pass
        return data_type

    # Public API

    def set_mask_for_data_type(self, data_type):
        """
        @param data_type:
        """

        if not data_type in (datetime.datetime, datetime.date, datetime.time):
            return
        conv = converter.get_converter(data_type)
        mask = conv.get_format()

        # For win32, skip mask
        # FIXME: How can we figure out the real locale specific string?
        if mask == '%X':
            mask = '%H:%M:%S'
        elif mask == '%x':
            mask = '%d/%m/%Y'
        elif mask == '%c':
            mask = '%d/%m/%Y %H:%M:%S'

        for format_char, mask_char in DATE_MASK_TABLE.items():
            mask = mask.replace(format_char, mask_char)

        self.set_mask(mask)

    #@deprecated('prefill')
    def set_completion_strings(self, strings=[], values=[]):
        """
        Set strings used for entry completion.
        If values are provided, each string will have an additional
        data type.

        @param strings:
        @type  strings: list of strings
        @param values:
        @type  values: list of values
        """

        completion = self._get_completion()
        model = completion.get_model()
        model.clear()

        if values:
            self._mode = ENTRY_MODE_DATA
            self.prefill(zip(strings, values))
        else:
            self._mode = ENTRY_MODE_TEXT
            self.prefill(strings)
    set_completion_strings = deprecated('prefill')(set_completion_strings)

    def set_text(self, text):
        """
        Sets the text of the entry

        @param text:
        """

        self._update_current_object(text)

        # If content isn't empty set_text emitts changed twice.
        # Protect content-changed from being updated and issue
        # a manual emission afterwards
        self._block_changed = True
        gtk.Entry.set_text(self, text)
        self._block_changed = False
        self.emit('content-changed')

        self.set_position(-1)

    def do_changed(self):
        if self._block_changed:
            self.emit_stop_by_name('changed')
            return
        self.emit('content-changed')

    # ProxyWidgetMixin implementation

    def read(self):
        mode = self._mode
        if mode == ENTRY_MODE_TEXT:
            text = self.get_text()
            try:
                return self._from_string(text)
            except ValidationError:
                # Do not consider masks which only displays static
                # characters invalid, instead return an empty string
                if self.get_mask() and text == self.get_empty_mask():
                    return ""
                else:
                    raise
        elif mode == ENTRY_MODE_DATA:
            return self._current_object
        else:
            raise AssertionError

    def update(self, data):
        if data is None:
            text = ""
        else:
            mode = self._mode
            if mode == ENTRY_MODE_DATA:
                new = self._get_text_from_object(data)
                if new is None:
                    raise TypeError("%r is not a data object" % data)
                text = new
            elif mode == ENTRY_MODE_TEXT:
                text = self._as_string(data)

        self.set_text(text)

type_register(ProxyEntry)

class Entry(ProxyEntry):
    def __init__(self, data_type=None):
        deprecationwarn('Entry is deprecated, use ProxyEntry instead',
                        stacklevel=3)
        ProxyEntry.__init__(self, data_type)
type_register(Entry)

class ProxyDateEntry(PropertyObject, DateEntry, ValidatableProxyWidgetMixin):
    __gtype_name__ = 'ProxyDateEntry'

    # changed allowed data types because checkbuttons can only
    # accept bool values
    allowed_data_types = datetime.date,

    def __init__(self):
        DateEntry.__init__(self)
        ValidatableProxyWidgetMixin.__init__(self)
        PropertyObject.__init__(self)

    gsignal('changed', 'override')
    def do_changed(self):
        self.chain()
        self.emit('content-changed')

    # ProxyWidgetMixin implementation

    def read(self):
        return self.get_date()

    def update(self, data):
        if data is None:
            self.entry.set_text("")
        else:
            self.set_date(data)

type_register(ProxyDateEntry)
