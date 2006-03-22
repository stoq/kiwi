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

import gettext
import string

import gobject
import pango
import gtk

from kiwi.ui.icon import IconEntry
from kiwi.utils import gsignal, gproperty, type_register

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

(COL_TEXT,
 COL_OBJECT) = range(2)

(ENTRY_MODE_TEXT,
 ENTRY_MODE_DATA) = range(2)

_ = lambda msg: gettext.dgettext('kiwi', msg)

class KiwiEntry(gtk.Entry):
    """
    The KiwiEntry is a Entry subclass with the following additions:

      - IconEntry, allows you to have an icon inside the entry
      - Mask, force the input to meet certain requirements
      - IComboMixin: Allows you work with objects instead of strings
        Adds a number of convenience methods such as L{prefill}().
    """
    __gtype_name__ = 'KiwiEntry'

    gproperty("completion", bool, False)
    gproperty('exact-completion', bool, default=False)
    gproperty("mask", str, default='')

    def __init__(self):
        gtk.Entry.__init__(self)

        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)

        self._current_object = None
        self._mode = ENTRY_MODE_TEXT
        self._icon = IconEntry(self)

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        self._block_insert = False
        self._block_delete = False

    # Virtual methods

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
        completion = self._get_completion()
        completion.set_match_func(match_func)

        return value

    def prop_set_completion(self, value):
        if not self.get_completion():
            self._enable_completion()
        return value

    def prop_set_mask(self, value):
        try:
            self.set_mask(value)
            return self.get_mask()
        except MaskError, e:
            pass
        return ''

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

    def set_exact_completion(self, value):
        """
        Enable exact entry completion.
        Exact means it needs to start with the value typed
        and the case needs to be correct.

        @param value: enable exact completion
        @type value:  boolean
        """

        self.exact_completion = value

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

    # IComboMixin

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

    def get_selected_label(self, treeiter):
        completion = self._get_completion()
        model = completion.get_model()
        return model[treeiter][COL_TEXT]

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
