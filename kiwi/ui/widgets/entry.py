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

"""GtkEntry support for the Kiwi Framework

The L{Entry} is also extended to provide an easy way to add entry completion
support and display an icon using L{kiwi.ui.icon.IconEntry}.
"""

import datetime
import gettext

import gtk

from kiwi.datatypes import ValidationError, converter, number
from kiwi.ui.entry import KiwiEntry
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import PropertyObject, gproperty, gsignal, type_register

_ = gettext.gettext

(COL_TEXT,
 COL_OBJECT) = range(2)

(ENTRY_MODE_TEXT,
 ENTRY_MODE_DATA) = range(2)

DATE_MASK_TABLE = {
    '%m': '%2d',
    '%y': '%2d',
    '%d': '%2d',
    '%Y': '%4d',
    }

class Entry(PropertyObject, KiwiEntry, WidgetMixinSupportValidation):
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

    gproperty("completion", bool, False)
    gproperty('exact-completion', bool, default=False)

    def __init__(self, data_type=None):
        KiwiEntry.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        PropertyObject.__init__(self, data_type=data_type)

        self._current_object = None
        self._entry_mode = ENTRY_MODE_TEXT

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

    # Properties
    def prop_set_exact_completion(self, value):
        if value:
            match_func = self._completion_exact_match_func
        else:
            match_func = self._completion_normal_match_func
        completion = self._create_completion()
        completion.set_match_func(match_func)

        return value

    def prop_set_completion(self, value):
        if not self.get_completion():
            self._enable_completion()
        return value

    def prop_set_data_type(self, data_type):
        data_type = super(Entry, self).prop_set_data_type(data_type)

        # Numbers should be right aligned
        if data_type and issubclass(data_type, number):
            self.set_property('xalign', 1.0)

        # Apply a mask for the data types, some types like
        # dates has a default mask
        self._set_mask_for_data_type(data_type)
        return data_type

    # Public API
    def set_exact_completion(self, value):
        """
        Enable exact entry completion.
        Exact means it needs to start with the value typed
        and the case needs to be correct.

        @param value: enable exact completion
        @type value:  boolean
        """

        self.exact_completion = value

    # XXX: Decide if this API or the Combobox prefill API should be used
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

        completion = self._create_completion()
        model = completion.get_model()
        model.clear()

        if values:
            if len(strings) != len(values):
                raise ValueError("values must have the same length as strings")

            for i, text in enumerate(strings):
                model.append([text, values[i]])
            self._entry_mode = ENTRY_MODE_DATA
        elif not strings:
            # This is considered disabling completion, PyGTK 2.8.1
            #self.set_completion(None)
            pass
        else:
            for s in strings:
                model.append([s, None])
            self._entry_mode = ENTRY_MODE_TEXT

    def set_text(self, text):
        """
        Sets the text of the entry

        @param text:
        """

        self._update_current_object(text)

        gtk.Entry.set_text(self, text)

        self.emit('content-changed')
        self.set_position(-1)

    # WidgetMixin implementation

    def read(self):
        mode = self._entry_mode
        if mode == ENTRY_MODE_TEXT:
            text = self.get_text()
            try:
                return self._from_string(text)
            except ValidationError:
                # Do not consider masks which only displays static
                # characters invalid, instead return an empty string
                if self._mask and text == self.get_empty_mask():
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
            mode = self._entry_mode
            if mode == ENTRY_MODE_DATA:
                new = self._get_text_from_object(data)
                if new is None:
                    raise TypeError("%r is not a data object" % data)
                text = new
            elif mode == ENTRY_MODE_TEXT:
                text = self._as_string(data)

        self.set_text(text)

    # Private

    def _set_mask_for_data_type(self, data_type):
        if not data_type in (datetime.datetime, datetime.date, datetime.time):
            return
        conv = converter.get_converter(data_type)
        mask = conv.get_format()

        # For win32, skip mask
        # FIXME: How can we figure out the real format string?
        for m in ('%X', '%x', '%c'):
            if m in mask:
                return

        for format_char, mask_char in DATE_MASK_TABLE.items():
            mask = mask.replace(format_char, mask_char)

        self.set_mask(mask)

    def _update_current_object(self, text):
        if self._entry_mode != ENTRY_MODE_DATA:
            return

        for row in self.get_completion().get_model():
            if row[COL_TEXT] == text:
                self._current_object = row[COL_OBJECT]
                break
        else:
            # Customized validation
            if text:
                self.set_invalid(_("'%s' is not a valid object" % text))
            elif self.mandatory:
                self.set_blank()
            else:
                self.set_valid()
            self._current_object = None

    def _get_text_from_object(self, obj):
        if self._entry_mode != ENTRY_MODE_DATA:
            return

        for row in self.get_completion().get_model():
            if row[COL_OBJECT] == obj:
                return row[COL_TEXT]

    def _create_completion(self):
        # Check so we have completion enabled, not this does not
        # depend on the property, the user can manually override it,
        # as long as there is a completion object set
        completion = self.get_completion()
        if completion:
            return completion

        return self._enable_completion()

    def _enable_completion(self):
        completion = gtk.EntryCompletion()
        self.set_completion(completion)
        completion.set_model(gtk.ListStore(str, object))
        completion.set_text_column(0)
        self.exact_completion = False
        completion.connect("match-selected",
                           self._on_completion__match_selected)
        self._current_object = None
        return completion

    def _completion_exact_match_func(self, completion, _, iter):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT]
        return self.get_text().startswith(content)

    def _completion_normal_match_func(self, completion, _, iter):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT].lower()
        return self.get_text().lower() in content

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        # this updates current_object and triggers content-changed
        self.set_text(model[iter][COL_TEXT])
        self.set_position(-1)
        # FIXME: Enable this at some point
        #self.activate()

type_register(Entry)
