#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006-2007 Async Open Source
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
#            Ronaldo Maia <romaia@async.com.br>
#

"""GtkEntry support for the Kiwi Framework"""

import datetime

import gobject
import pango

from kiwi.datatypes import converter, number, ValueUnset, currency
from kiwi.decorators import deprecated
from kiwi.enums import Alignment
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.python import deprecationwarn
from kiwi.ui.entry import MaskError, KiwiEntry, ENTRY_MODE_TEXT, \
     ENTRY_MODE_DATA
from kiwi.ui.dateentry import DateEntry
from kiwi.ui.proxywidget import ValidatableProxyWidgetMixin, \
     VALIDATION_ICON_WIDTH
from kiwi.utils import gsignal, type_register

class ProxyEntryMeta(gobject.GObjectMeta):
    def __call__(self, *args, **kwargs):
        rv = super(ProxyEntryMeta, self).__call__(*args, **kwargs)
        rv.__post_init__()
        return rv

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

    __class__ = ProxyEntryMeta

    allowed_data_types = (basestring, datetime.date, datetime.time,
                          datetime.datetime, object) + number

    __gtype_name__ = 'ProxyEntry'
    mandatory = gobject.property(type=bool, default=False)
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self, data_type=None):
        self._block_changed = False
        self._has_been_updated = False
        KiwiEntry.__init__(self)
        ValidatableProxyWidgetMixin.__init__(self)
        self._entry_data_type = data_type
        # XXX: Sales -> New Loan Item requires this, figure out why
        try:
            self.props.data_type = data_type
        except (AttributeError, TypeError):
            pass
        # Hide currency symbol from the entry.
        self.set_options_for_datatype(currency, symbol=False)

    def __post_init__(self):
        self.props.data_type = self._entry_data_type

    # Virtual methods
    gsignal('changed', 'override')
    def do_changed(self):
        if self._block_changed:
            self.emit_stop_by_name('changed')
            return
        self._update_current_object(self.get_text())
        self.emit('content-changed')

    def _set_data_type(self, data_type):
        if not ProxyWidgetMixin.set_data_type(self, data_type):
            return

        # Numbers and dates should be right aligned
        conv = converter.get_converter(data_type)
        if conv.align == Alignment.RIGHT:
            self.set_property('xalign', 1.0)

        # Apply a mask for the data types, some types like
        # dates has a default mask
        try:
            self.set_mask_for_data_type(data_type)
        except MaskError:
            pass

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=_set_data_type,
        type=str, blurb='Data Type')

    # Public API

    def set_mask_for_data_type(self, data_type):
        """
        Set a mask for the parameter data_type.
        @param data_type:
        """
        conv = converter.get_converter(data_type)
        mask = conv.get_mask()
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

        completion = self._get_entry_completion()
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

        self._has_been_updated = True
        self._update_current_object(text)

        # If content isn't empty set_text emitts changed twice.
        # Protect content-changed from being updated and issue
        # a manual emission afterwards
        self._block_changed = True
        KiwiEntry.set_text(self, text)
        self._block_changed = False
        self.emit('content-changed')

        self.set_position(-1)

    # ProxyWidgetMixin implementation

    def read(self):
        mode = self._mode
        if mode == ENTRY_MODE_TEXT:
            # Do not consider masks which only displays static
            # characters invalid, instead return None
            if not self._has_been_updated:
                return ValueUnset
            text = self.get_text()
            return self._from_string(text)
        elif mode == ENTRY_MODE_DATA:
            return self._current_object
        else:
            raise AssertionError

    def update(self, data):
        if data is ValueUnset:
            self.set_text("")
            self._has_been_updated = False
        elif data is None:
            self.set_text("")
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

class ProxyDateEntry(DateEntry, ValidatableProxyWidgetMixin):
    __gtype_name__ = 'ProxyDateEntry'

    # changed allowed data types because checkbuttons can only
    # accept bool values
    allowed_data_types = datetime.date,

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self):
        DateEntry.__init__(self)
        ValidatableProxyWidgetMixin.__init__(self)

        # Add some space to the entry, so it has rom for the icon, in case
        # of a validation error.
        #
        # Since we set the widget's width based on the number of characters,
        # get the width of a single char, so we can calculate how many
        # 'chars' the icon takes.
        layout = self.entry.get_layout()
        context = layout.get_context()
        metrics = context.get_metrics(context.get_font_description())
        char_width =  metrics.get_approximate_char_width() / pango.SCALE
        current_width = self.entry.get_width_chars()

        # We add 4 pixels to the width, because of the icon borders
        icon_width = VALIDATION_ICON_WIDTH + 4
        self.entry.set_width_chars(current_width
                                   + int(icon_width / char_width))

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

    def _get_mandatory(self):
        return self.entry.props.mandatory

    def _set_mandatory(self, value):
        self.entry.props.mandatory = value
    mandatory = gobject.property(getter=_get_mandatory,
                                 setter=_set_mandatory,
                                 type=bool, default=False)

    # ValidatableProxyWidgetMixin

    # Since the widget that should be marked as valid/invalid is the entry,
    # we also call those methods for self.entry
    def set_valid(self):
        ValidatableProxyWidgetMixin.set_valid(self)
        self.entry.set_valid()

    def set_invalid(self, text=None, fade=True):
        ValidatableProxyWidgetMixin.set_invalid(self, text, fade)
        self.entry.set_invalid(text, fade)

    def set_blank(self):
        ValidatableProxyWidgetMixin.set_blank(self)
        self.entry.set_blank()

    def get_background(self):
        return self.entry.get_background()

type_register(ProxyDateEntry)
