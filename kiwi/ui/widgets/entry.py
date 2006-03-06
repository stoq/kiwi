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
from kiwi.ui.entry import MaskError, KiwiEntry
from kiwi.ui.dateentry import DateEntry
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
    '%H': '%2d',
    '%M': '%2d',
    '%S': '%2d',
    '%T': '%2d:%2d:%2d',
    # FIXME: locale specific
    '%r': '%2d:%2d:%2d %2c',
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
    gproperty("mask", str, default='')

    def __init__(self, data_type=None):
        KiwiEntry.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        PropertyObject.__init__(self, data_type=data_type)

        self._current_object = None
        self._mode = ENTRY_MODE_TEXT

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
        completion = self._get_completion()
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
        try:
            self._set_mask_for_data_type(data_type)
        except MaskError:
            pass
        return data_type

    # Properties

    def prop_set_mask(self, value):
        try:
            self.set_mask(value)
            return self.get_mask()
        except MaskError, e:
            pass
        return ''

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
        print 'set_completion_strings() is deprecated, use prefill()'

        completion = self._get_completion()
        model = completion.get_model()
        model.clear()

        if values:
            self._mode = ENTRY_MODE_DATA
            self.prefill(zip(strings, values))
        else:
            self._mode = ENTRY_MODE_TEXT
            self.prefill(strings)

    def prefill(self, itemdata, sort=False):
        """Fills the Combo with listitems corresponding to the itemdata
        provided.

        Parameters:
          - itemdata is a list of strings or tuples, each item corresponding
            to a listitem. The simple list format is as follows::

            >>> [ label0, label1, label2 ]

            If you require a data item to be specified for each item, use a
            2-item tuple for each element. The format is as follows::

            >>> [ ( label0, data0 ), (label1, data1), ... ]

          - Sort is a boolean that specifies if the list is to be sorted by
            label or not. By default it is not sorted
        """
        if not isinstance(itemdata, (list, tuple)):
            raise TypeError("'data' parameter must be a list or tuple of item "
                            "descriptions, found %s") % type(itemdata)

        completion = self._get_completion()
        model = completion.get_model()

        if len(itemdata) == 0:
            model.clear()
            return

        if (len(itemdata) > 0 and
            type(itemdata[0]) in (tuple, list) and
            len(itemdata[0]) == 2):
            mode = self._mode = ENTRY_MODE_DATA
        else:
            mode = self._mode

        values = {}
        if mode == ENTRY_MODE_TEXT:
            if sort:
                itemdata.sort()

            for item in itemdata:
                if item in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[item] = None

                model.append((item, None))
        elif mode == ENTRY_MODE_DATA:
            if sort:
                itemdata.sort(lambda x, y: cmp(x[0], y[0]))

            for item in itemdata:
                text, data = item
                if text in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[text] = None
                model.append((text, data))
        else:
            raise TypeError("Incorrect format for itemdata; see "
                            "docstring for more information")

    def get_iter_by_data(self, data):
        if self._mode != ENTRY_MODE_DATA:
            raise TypeError(
                "select_item_by_data can only be used in data mode")

        completion = self._get_completion()
        model = completion.get_model()

        for row in model:
            if row[COL_OBJECT] == data:
                return row.iter
                break
        else:
            raise KeyError("No item correspond to data %r in the combo %s"
                           % (data, self.name))

    def get_iter_by_label(self, label):
        completion = self._get_completion()
        model = completion.get_model()
        for row in model:
            if row[COL_TEXT] == label:
                return row.iter
        else:
            raise KeyError("No item correspond to label %r in the combo %s"
                           % (label, self.name))

    def get_selected_by_iter(self, treeiter):
        completion = self._get_completion()
        model = completion.get_model()
        mode = self._mode
        if mode == ENTRY_MODE_TEXT:
            return model[treeiter][COL_TEXT]
        elif mode == ENTRY_MODE_DATA:
            return model[treeiter][COL_OBJECT]
        else:
            raise AssertionError

    def get_iter_from_obj(self, obj):
        mode = self._mode
        if mode == ENTRY_MODE_TEXT:
            return self.get_iter_by_label(obj)
        elif mode == ENTRY_MODE_DATA:
            return self.get_iter_by_data(obj)
        else:
            # XXX: When setting the datatype to non string, automatically go to
            #      data mode
            raise TypeError("unknown Entry mode. Did you call prefill?")

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
        if self._mode != ENTRY_MODE_DATA:
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
        if self._mode != ENTRY_MODE_DATA:
            return

        for row in self.get_completion().get_model():
            if row[COL_OBJECT] == obj:
                return row[COL_TEXT]

    def _get_completion(self):
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

class ProxyDateEntry(PropertyObject, DateEntry, WidgetMixinSupportValidation):
    __gtype_name__ = 'ProxyDateEntry'

    # changed allowed data types because checkbuttons can only
    # accept bool values
    allowed_data_types = datetime.date,

    def __init__(self):
        DateEntry.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        PropertyObject.__init__(self)

    gproperty("mask", str, default='')
    def prop_set_mask(self, value):
        try:
            self.entry.set_mask(value)
            mask = self.entry.get_mask()
        except MaskError, e:
            mask = ''
        return mask

    # WidgetMixin implementation

    def read(self):
        return self.entry.get_date()

    def update(self, data):
        if data is None:
            self.entry.set_text("")
        else:
            self.set_date(data)

type_register(ProxyDateEntry)
