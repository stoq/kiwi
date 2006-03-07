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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""
An enchanced version of GtkEntry that supports icons and masks
"""

import datetime
import string

import gobject
import pango
import gtk

from kiwi.datatypes import converter
from kiwi.ui.icon import IconEntry
from kiwi.utils import gsignal, type_register

class MaskError(Exception):
    pass

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
    '%H': '%2d',
    '%M': '%2d',
    '%S': '%2d',
    '%T': '%2d:%2d:%2d',
    # FIXME: locale specific
    '%r': '%2d:%2d:%2d %2c',
    }

class KiwiEntry(gtk.Entry):
    __gtype_name__ = 'KiwiEntry'

    def __init__(self):
        gtk.Entry.__init__(self)

        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)

        self._icon = IconEntry(self)

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        self._block_insert = False
        self._block_delete = False

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

        self.set_text("")
        self._insert_mask(0, input_length)
        self._mask = mask

    def set_mask_for_data_type(self, data_type):
        """
        @param: data_type
        """

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

    def get_mask(self):
        """
        @returns: the mask
        """
        return self._mask

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

    def get_empty_mask(self, start=None, end=None):
        """
        Gets the empty mask between start and end

        @param start:
        @param end:
        @returns: mask
        @rtype: string
        """

        if start is None:
            start = 0
        if end is None:
            end = len(self._mask_validators)

        s = ''
        for validator in self._mask_validators[start:end]:
            if isinstance(validator, int):
                s += ' '
            elif isinstance(validator, str):
                s += validator
            else:
                raise AssertionError
        return s

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
        text = self.get_empty_mask(start, end)
        self._really_insert_text(text, position=start)

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

    # IconEntry

    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)

    def update_background(self, color):
        self._icon.update_background(color)

    def get_icon_window(self):
        return self._icon.get_icon_window()

type_register(KiwiEntry)

def main(args):
    win = gtk.Window()
    win.set_title('gtk.Entry subclass')
    def cb(window, event):
        print 'fields', widget.get_field_text()
        gtk.main_quit()
    win.connect('delete-event', cb)

    widget = KiwiEntry()
    widget.set_mask('%3d.%3d.%3d.%3d')

    win.add(widget)

    win.show_all()

    widget.select_region(0, 0)
    gtk.main()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
