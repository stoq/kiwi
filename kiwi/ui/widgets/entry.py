#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
import string

import gobject
import pango
import gtk

from kiwi.datatypes import converter
from kiwi.ui.icon import IconEntry
from kiwi.ui.widgets.proxy import WidgetMixinSupportValidation
from kiwi.utils import PropertyObject, gproperty, gsignal, type_register

_ = gettext.gettext

class MaskError(Exception):
    pass

(COL_TEXT,
 COL_OBJECT) = range(2)

(ENTRY_MODE_TEXT,
 ENTRY_MODE_DATA) = range(2)

(INPUT_CHARACTER,
 INPUT_ALPHA,
 INPUT_DIGIT) = range(3)

INPUT_FORMATS = {
    'a': INPUT_ALPHA,
    'd': INPUT_DIGIT,
    'c': INPUT_CHARACTER,
    }

DATE_MASK_TABLE = {
    '%m': '%2d',
    '%y': '%2d',
    '%d': '%2d',
    '%Y': '%4d',
    # For win32
    # FIXME: How can we figure out the real format string?
    '%X': '%2d:%2d:%2d',
    '%x': '%4d-%2d-%2d',
    '%c': '%4d-%2d-%2d %2d:%2d:%2d',
    }

class Entry(PropertyObject, gtk.Entry, WidgetMixinSupportValidation):
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
        gtk.Entry.__init__(self)
        WidgetMixinSupportValidation.__init__(self)
        PropertyObject.__init__(self, data_type=data_type)
        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)

        self._current_object = None
        self._entry_mode = ENTRY_MODE_TEXT
        self._icon = IconEntry(self)

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        self._block_insert = False
        self._block_delete = False

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

    gsignal('size-allocate', 'override')
    def do_size_allocate(self, allocation):
        #gtk.Entry.do_size_allocate(self, allocation)
        self.chain(allocation)

        if self.flags() & gtk.REALIZED:
            self._icon.resize_windows()

    def do_expose_event(self, event):
        gtk.Entry.do_expose_event(self, event)

        if event.window == self.window:
            self._icon.draw_pixbuf()

    def do_realize(self):
        gtk.Entry.do_realize(self)
        self._icon.construct()

    def do_unrealize(self):
        self._icon.deconstruct()
        gtk.Entry.do_unrealize(self)


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

    def prop_set_mask(self, value):
        try:
            self.set_mask(value)
            return self._mask
        except MaskError, e:
            pass
        return ''

    def prop_set_data_type(self, value):
        value = super(Entry, self).prop_set_data_type(value)

        # Apply a mask for the data types, some types like
        # dates has a default mask
        self._set_mask_for_data_type(value)
        return value

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

    # Public API

    def set_mask(self, mask):
        """
        Sets the mask of the Entry.
        The format of the mask is similar to printf, but the
        only supported format characters are:
        - 'd' digit
        - 'a' alphabet, honors the locale
        - 'c' any character
        A digit is supported after the control.
        Example mask for a ISO-8601 date
        >>> entry.set_mask('%4d-%2d-%2d')

        @param mask: the mask to set
        """

        if not mask:
            self.modify_font(pango.FontDescription("sans"))
            self._mask = mask
            return

        input_length = len(mask)
        lenght = 0
        pos = 0
        while True:
            if pos >= input_length:
                break
            if mask[pos] == '%':
                s = ''
                format_char = None
                # Validate/extract format mask
                pos += 1
                while True:
                    if pos >= len(mask):
                        raise MaskError("Invalid mask: %s" % mask)

                    if mask[pos] in INPUT_FORMATS:
                        format_char = mask[pos]
                        break

                    if mask[pos] not in string.digits:
                        raise MaskError(
                            "invalid format padding character: %s" % mask[pos])
                    s += mask[pos]
                    pos += 1
                    if pos >= len(mask):
                        raise MaskError("Invalid mask: %s" % mask)

                # If there a none specificed, assume 1, follows printf
                try:
                    chars = int(s)
                except ValueError:
                    chars = 1
                self._mask_validators += [INPUT_FORMATS[format_char]] * chars
            else:
                self._mask_validators.append(mask[pos])
            pos += 1

        self.modify_font(pango.FontDescription("monospace"))

        self._insert_mask(0, input_length)
        self._mask = mask

    def get_field_text(self):
        """
        Get the fields assosiated with the entry.
        A field is dynamic content separated by static.
        For example, the format string %3d-%3d has two fields
        separated by a dash.
        if a field is empty it'll return an empty string
        otherwise it'll include the content

        @returns: fields
        @rtype: list of strings
        """
        if not self._mask:
            raise MaskError("a mask must be set before calling get_field_text")

        def append_field(fields, field_type, s):
            if s.count(' ') == len(s):
                s = ''
            if field_type == INPUT_DIGIT:
                try:
                    s = int(s)
                except ValueError:
                    s = None
            fields.append(s)

        fields = []
        pos = 0
        s = ''
        field_type = -1
        text = self.get_text()
        validators = self._mask_validators
        while True:
            if pos >= len(validators):
                append_field(fields, field_type, s)
                break

            validator = validators[pos]
            if isinstance(validator, int):
                try:
                    s += text[pos]
                except IndexError:
                    s = ''
                field_type = validator
            else:
                append_field(fields, field_type, s)
                s = ''
                field_type = -1
            pos += 1

        return fields

    def set_text(self, text):
        """
        Sets the text of the entry

        @param text:
        """

        self._update_current_object(text)

        gtk.Entry.set_text(self, text)

        self.emit('content-changed')

    # WidgetMixin implementation
    def read(self):
        mode = self._entry_mode
        if mode == ENTRY_MODE_TEXT:
            return self._from_string(self.get_text())
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

    def _really_delete_text(self, start, end):
        # A variant of delete_text() that never is blocked by us
        self._block_delete = True
        self.delete_text(start, end)
        self._block_delete = False

    def _really_insert_text(self, text, position):
        # A variant of insert_text() that never is blocked by us
        self._block_insert = True
        self.insert_text(text, position)
        self._block_insert = False

    def _insert_mask(self, start, end):
        s = ''
        for validator in self._mask_validators[start:end]:
            if isinstance(validator, int):
                s += ' '
            elif isinstance(validator, str):
                s += validator
            else:
                raise AssertionError

        self._really_insert_text(s, position=start)

    def _confirms_to_mask(self, position, text):
        validators = self._mask_validators
        if position >= len(validators):
            return False

        validator = validators[position]
        if validator == INPUT_ALPHA:
            if not text in string.lowercase:
                return False
        elif validator == INPUT_DIGIT:
            if not text in string.digits:
                return False
        elif isinstance(validator, str):
            if validator == text:
                return True
            return False
        elif validator == INPUT_CHARACTER:
            # Accept anything
            pass

        return True

    def _set_mask_for_data_type(self, data_type):
        if not data_type in (datetime.datetime, datetime.date, datetime.time):
            return
        conv = converter.get_converter(data_type)
        mask = conv.get_format()
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

    # Callbacks

    def _on_insert_text(self, editable, new, length, position):
        if not self._mask or self._block_insert:
            return

        position = self.get_position()
        for inc, c in enumerate(new):
            if not self._confirms_to_mask(position + inc, c):
                self.stop_emission('insert-text')
                return

            self._really_delete_text(position, position+1)

        # If the next character is a static character and
        # the one after the next is input, skip over
        # the static character
        next = position + 1
        validators = self._mask_validators
        if len(validators) > next + 1:
            if (isinstance(validators[next], str) and
                isinstance(validators[next+1], int)):
                # Ugly: but it must be done after the entry
                #       inserts the text
                gobject.idle_add(self.set_position, next+1)

    def _on_delete_text(self, editable, start, end):
        if not self._mask or self._block_delete:
            return

        # This is tricky, quite ugly but it works.
        # We want to insert the mask after the delete is done
        # Instead of using idle_add we delete the text first
        # insert our mask afterwards and finally blocks the call
        # from happing in the entry itself
        self._really_delete_text(start, end)
        self._insert_mask(start, end)

        self.stop_emission('delete-text')

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        # this updates current_object and triggers content-changed
        self.set_text(model[iter][COL_TEXT])
        self.set_position(-1)
        # FIXME: Enable this at some point
        #self.activate()

    # IconEntry

    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)

    def update_background(self, color):
        self._icon.update_background(color)

    def get_icon_window(self):
        return self._icon.get_icon_window()

type_register(Entry)

def main(args):
    win = gtk.Window()
    win.set_title('gtk.Entry subclass')
    def cb(window, event):
        print 'fields', widget.get_field_text()
        gtk.main_quit()
    win.connect('delete-event', cb)

    widget = Entry()
    widget.set_mask('%3d.%3d.%3d.%3d')

    win.add(widget)

    win.show_all()

    widget.select_region(0, 0)
    gtk.main()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
