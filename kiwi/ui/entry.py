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
#            Ronaldo Maia <romaia@async.com.br>
#
#
# Design notes:
#
#   When inserting new text, supose, the entry, at some time is like this,
#   ahd the user presses '0', for instance:
#   --------------------------------
#   | ( 1 2 )   3 4 5   - 6 7 8 9  |
#   --------------------------------
#              ^ ^     ^
#              S P     E
#
#   S - start of the field (start)
#   E - end of the field (end)
#   P - pos - where the new text is being inserted. (pos)
#
#   So, the new text will be:
#
#     the old text, from 0 until P
#   + the new text
#   + the old text, from P until the end of the field, shifted to the
#     right
#   + the old text, from the end of the field, to the end of the text.
#
#   After inserting, the text will be this:
#   --------------------------------
#   | ( 1 2 )   3 0 4 5 - 6 7 8 9  |
#   --------------------------------
#              ^   ^   ^
#              S   P   E
#
#
#   When deleting some text, supose, the entry, at some time is like this:
#   --------------------------------
#   | ( 1 2 )   3 4 5 6 - 7 8 9 0  |
#   --------------------------------
#              ^ ^ ^   ^
#              S s e   E
#
#   S - start of the field (_start)
#   E - end of the field (_end)
#   s - start of the text being deleted (start)
#   e - end of the text being deleted (end)
#
#   end - start -> the number of characters being deleted.
#
#   So, the new text will be:
#
#     the old text, from 0 until the start of the text being deleted.
#   + the old text, from the start of where the text is being deleted, until
#     the end of the field, shifted to the left, end-start positions
#   + the old text, from the end of the field, to the end of the text.
#
#   So, after the text is deleted, the entry will look like this:
#
#   --------------------------------
#   | ( 1 2 )   3 5 6   - 7 8 9 0  |
#   --------------------------------
#                ^
#                P
#
#   P = the position of the cursor after the deletion, witch is equal to
#   start (s at the previous illustration)


"""
An enchanced version of GtkEntry that supports icons and masks
"""

import gettext
import string
try:
    set
except NameError:
    from sets import Set as set

import gobject
import pango
import gtk

from kiwi.enums import Direction
from kiwi.ui.entrycompletion import KiwiEntryCompletion
from kiwi.utils import type_register

# In gtk+ 2.18 they refactored gtk.Entry to use gtk.EntryBuffer, so we need to
# track the gtk version here for later use.
if gtk.gtk_version >= (2, 18):
    GTK_2_18 = True
else:
    GTK_2_18 = False


class MaskError(Exception):
    pass

(INPUT_ASCII_LETTER,
 INPUT_ALPHA,
 INPUT_ALPHANUMERIC,
 INPUT_DIGIT) = range(4)

INPUT_FORMATS = {
    '0': INPUT_DIGIT,
    'L': INPUT_ASCII_LETTER,
    'A': INPUT_ALPHANUMERIC,
    'a': INPUT_ALPHANUMERIC,
    '&': INPUT_ALPHA,
    }

# Todo list: Other usefull Masks
#  9 - Digit, optional
#  ? - Ascii letter, optional
#  C - Alpha, optional

INPUT_CHAR_MAP = {
    INPUT_ASCII_LETTER:     lambda text: text in string.ascii_letters,
    INPUT_ALPHA:            unicode.isalpha,
    INPUT_ALPHANUMERIC:     unicode.isalnum,
    INPUT_DIGIT:            unicode.isdigit,
    }


(COL_TEXT,
 COL_OBJECT) = range(2)

(ENTRY_MODE_UNKNOWN,
 ENTRY_MODE_TEXT,
 ENTRY_MODE_DATA) = range(3)

_ = lambda msg: gettext.dgettext('kiwi', msg)

class KiwiEntry(gtk.Entry):
    """
    The KiwiEntry is a Entry subclass with the following additions:

      - Mask, force the input to meet certain requirements
      - IComboMixin: Allows you work with objects instead of strings
        Adds a number of convenience methods such as L{prefill}().
    """
    __gtype_name__ = 'KiwiEntry'

    def __init__(self):
        self._completion = None

        gtk.Entry.__init__(self)
        self._update_position()
        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)
        self.connect_after('grab-focus', self._after_grab_focus)

        self.connect('changed', self._on_changed)

        self.connect('focus', self._on_focus)
        self.connect('focus-out-event', self._on_focus_out_event)
        self.connect('move-cursor', self._on_move_cursor)

        # Ideally, this should be connected to notify::cursor-position, but
        # there seems to be a bug in gtk that the notification is not emited
        # when it should.
        # TODO: investigate that and report a bug.
        self.connect('notify::selection-bound',
                     self._on_notify_selection_bound)
        self.connect('notify::xalign', self._on_notify_xalign)

        self._block_changed = False

        self._current_object = None
        self._mode = ENTRY_MODE_TEXT

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        # Fields defined by mask
        # each item is a tuble, containing the begining and the end of the
        # field in the text
        self._mask_fields = []
        self._current_field = -1
        self._pos = 0
        self._selecting = False
        self._prop_completion = False
        self._exact_completion = False
        self._block_insert = False
        self._block_delete = False

    # Properties

    def _get_exact_completion(self):
        return self._exact_completion

    def _set_exact_completion(self, value):
        self.set_exact_completion(value)
        self._exact_completion = value
    exact_completion = gobject.property(getter=_get_exact_completion,
                                        setter=_set_exact_completion,
                                        type=bool, default=False)

    def _prop_get_completion(self):
        return self._prop_completion

    def _prop_set_completion(self, value):
        if not self.get_completion():
            self.set_completion(gtk.EntryCompletion())
        self._prop_completion = value
    completion = gobject.property(getter=_prop_get_completion,
                                  setter=_prop_set_completion,
                                  type=bool, default=False)

    def _get_mask(self):
        return self._mask

    def _set_mask(self, value):
        try:
            self.set_mask(value)
            return self.get_mask()
        except MaskError, e:
            pass
    mask = gobject.property(getter=_get_mask,
                            setter=_set_mask,
                            type=str, default='')

    # Public API
    def set_text(self, text):
        completion = self.get_completion()

        if isinstance(completion, KiwiEntryCompletion):
            self.handler_block(completion.changed_id)

        gtk.Entry.set_text(self, text)

        if GTK_2_18:
            self._do_2_18_workaround(text)

        if isinstance(completion, KiwiEntryCompletion):
            self.handler_unblock(completion.changed_id)

    def _do_2_18_workaround(self, text):
        # FIXME: When using gtk 2.18 and pygtk 2.16 our set_text method is
        # broken because we edit the text that will stay in the entry (mask
        # feature). My guess is that the signal 'insert-text' have not been
        # emitted when calling gtk_entry_set_text method (but the signal is
        # emitted in gtk_entry_insert_text method, see gtkentry.c in gtk+).

        self._really_delete_text(0, -1)
        if not self._mask:
            new_text = text
            self._really_insert_text(text, 0)
            return

        if not text:
            # set_text used to clean the entry, but the mask must stay there.
            self._really_insert_text(self.get_empty_mask(), 0)
            return

        to_insert = []
        for i in self._mask_validators:
            if isinstance(i, int):
                # mark available positions with an empty string
                to_insert.append('')
            else:
                to_insert.append(i)

        for t in unicode(text):
            # find the next position available for insertion
            for pos, k in enumerate(to_insert):
                if k == '':
                    break

            if self._confirms_to_mask(pos, t):
                to_insert[pos] = t

        self._really_insert_text(''.join(to_insert), 0)
        self.set_position(pos+1)

    # Mask & Fields

    def set_mask(self, mask):
        """
        Sets the mask of the Entry.
        Supported format characters are:
          - '0' digit
          - 'L' ascii letter (a-z and A-Z)
          - '&' alphabet, honors the locale
          - 'a' alphanumeric, honors the locale
          - 'A' alphanumeric, honors the locale

        This is similar to MaskedTextBox:
        U{http://msdn2.microsoft.com/en-us/library/system.windows.forms.maskedtextbox.mask(VS.80).aspx}

        Example mask for a ISO-8601 date
        >>> entry.set_mask('0000-00-00')

        @param mask: the mask to set
        """

        if not mask:
            self.modify_font(pango.FontDescription("sans"))
            self._mask = mask
            return

        # First, reset
        self._mask_validators = []
        self._mask_fields = []
        self._current_field = -1

        mask = unicode(mask)
        input_length = len(mask)
        lenght = 0
        pos = 0
        field_begin = 0
        field_end = 0
        while True:
            if pos >= input_length:
                break
            if mask[pos] in INPUT_FORMATS:
                self._mask_validators += [INPUT_FORMATS[mask[pos]]]
                field_end += 1
            else:
                self._mask_validators.append(mask[pos])
                if field_begin != field_end:
                    self._mask_fields.append((field_begin, field_end))
                field_end += 1
                field_begin = field_end
            pos += 1

        self._mask_fields.append((field_begin, field_end))
        self.modify_font(pango.FontDescription("monospace"))

        self._really_delete_text(0, -1)
        self._insert_mask(0, input_length)
        self._mask = mask

    def get_mask(self):
        """
        Get the mask.
        @returns: the mask
        """
        return self._mask

    def get_field_text(self, field):
        if not self._mask:
            raise MaskError("a mask must be set before calling get_field_text")

        text = self.get_text()
        start, end = self._mask_fields[field]
        return text[start: end].strip()

    def get_fields(self):
        """
        Get the fields assosiated with the entry.
        A field is dynamic content separated by static.
        For example, the format string 000-000 has two fields
        separated by a dash.
        if a field is empty it'll return an empty string
        otherwise it'll include the content

        @returns: fields
        @rtype: list of strings
        """
        if not self._mask:
            raise MaskError("a mask must be set before calling get_fields")

        fields = []

        text = unicode(self.get_text())
        for start, end in self._mask_fields:
            fields.append(text[start:end].strip())

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
            elif isinstance(validator, unicode):
                s += validator
            else:
                raise AssertionError
        return s

    def get_field_pos(self, field):
        """
        Get the position at the specified field.
        """
        if field >= len(self._mask_fields):
            return None

        start, end = self._mask_fields[field]

        return start

    def _get_field_ideal_pos(self, field):
        start, end = self._mask_fields[field]
        text = self.get_field_text(field)
        pos = start+len(text)
        return pos

    def get_field(self):
        if self._current_field >= 0:
            return self._current_field
        else:
            return None

    def set_field(self, field, select=False):
        if field >= len(self._mask_fields):
            return

        pos = self._get_field_ideal_pos(field)
        self.set_position(pos)

        if select:
            field_text = self.get_field_text(field)
            start, end = self._mask_fields[field]
            self.select_region(start, pos)

        self._current_field = field

    def get_field_length(self, field):
        if 0 <= field < len(self._mask_fields):
            start, end = self._mask_fields[field]
            return end - start

    def _shift_text(self, start, end, direction=Direction.LEFT,
                    positions=1):
        """
        Shift the text, to the right or left, n positions. Note that this
        does not change the entry text. It returns the shifted text.

        @param start:
        @param end:
        @param direction:   see L{kiwi.enums.Direction}
        @param positions:   the number of positions to shift.

        @return:        returns the text between start and end, shifted to
                        the direction provided.
        """
        text = self.get_text()
        new_text = ''
        validators = self._mask_validators

        if direction == Direction.LEFT:
            i = start
        else:
            i = end - 1

        # When shifting a text, we wanna keep the static chars where they
        # are, and move the non-static chars to the right position.
        while start <= i < end:
            if isinstance(validators[i], int):
                # Non-static char shoud be here. Get the next one (depending
                # on the direction, and the number of positions to skip.)
                #
                # When shifting left, the next char will be on the right,
                # so, it will be appended, to the new text.
                # Otherwise, when shifting right, the char will be
                # prepended.
                next_pos = self._get_next_non_static_char_pos(i, direction,
                                                              positions-1)

                # If its outside the bounds of the region, ignore it.
                if not start <= next_pos <= end:
                    next_pos = None

                if next_pos is not None:
                    if direction == Direction.LEFT:
                        new_text = new_text + text[next_pos]
                    else:
                        new_text = text[next_pos] + new_text
                else:
                    if direction == Direction.LEFT:
                        new_text = new_text + ' '
                    else:
                        new_text = ' ' + new_text

            else:
                # Keep the static char where it is.
                if direction == Direction.LEFT:
                   new_text = new_text + text[i]
                else:
                   new_text = text[i] + new_text
            i += direction

        return new_text

    def _get_next_non_static_char_pos(self, pos, direction=Direction.LEFT,
                                      skip=0):
        """
        Get next non-static char position, skiping some chars, if necessary.
        @param skip:        skip first n chars
        @param direction:   direction of the search.
        """
        text = self.get_text()
        validators = self._mask_validators
        i = pos+direction+skip
        while 0 <= i < len(text):
            if isinstance(validators[i], int):
                return i
            i += direction

        return None

    def _get_field_at_pos(self, pos, dir=None):
        """
        Return the field index at position pos.
        """
        for p in self._mask_fields:
            if p[0] <= pos <= p[1]:
                return self._mask_fields.index(p)

        return None

    def set_exact_completion(self, value):
        """
        Enable exact entry completion.
        Exact means it needs to start with the value typed
        and the case needs to be correct.

        @param value: enable exact completion
        @type value:  boolean
        """

        if value:
            match_func = self._completion_exact_match_func
        else:
            match_func = self._completion_normal_match_func
        completion = self._get_entry_completion()
        completion.set_match_func(match_func)

    def is_empty(self):
        text = self.get_text()
        if self._mask:
            empty = self.get_empty_mask()
        else:
            empty = ''

        return text == empty

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
        if position < 0 or position >= len(validators):
            return False

        validator = validators[position]
        if isinstance(validator, int):
            if not INPUT_CHAR_MAP[validator](text):
                return False
        if isinstance(validator, unicode):
            if validator == text:
                return True
            return False

        return True

    def _update_current_object(self, text):
        if self._mode != ENTRY_MODE_DATA:
            return

        self._current_object = None
        for row in self.get_completion().get_model():
            if row[COL_TEXT] == text:
                self._current_object = row[COL_OBJECT]
                break

        treeview = self.get_completion().get_treeview()
        model = treeview.get_model()
        selection = treeview.get_selection()
        if self._current_object:
            treeiter = row.iter

            if isinstance(model, gtk.TreeModelFilter) and treeiter:
                # Just like we do in comboentry.py, convert iter between
                # models. See #3099 for mor information
                tmodel = model.get_model()
                if tmodel.iter_is_valid(treeiter):
                    treeview.set_model(tmodel)
                    selection = treeview.get_selection()
                else:
                    treeiter = model.convert_child_iter_to_iter(treeiter)

            selection.select_iter(treeiter)

            self.set_valid()
        elif text:
            selection.unselect_all()
            self.set_invalid(_("'%s' is not a valid object" % text))
        elif self.mandatory:
            selection.unselect_all()
            self.set_blank()

    def _get_text_from_object(self, obj):
        if self._mode != ENTRY_MODE_DATA:
            return

        for row in self.get_completion().get_model():
            if row[COL_OBJECT] == obj:
                return row[COL_TEXT]

    def _get_entry_completion(self):
        # Check so we have completion enabled, not this does not
        # depend on the property, the user can manually override it,
        # as long as there is a completion object set
        completion = self.get_completion()
        if completion:
            return completion

        completion = gtk.EntryCompletion()
        self.set_completion(completion)
        return completion

    def get_completion(self):
        return self._completion

    def set_completion(self, completion):
        if not isinstance(completion, KiwiEntryCompletion):
            gtk.Entry.set_completion(self, completion)
            completion.set_model(gtk.ListStore(str, object))
            completion.set_text_column(0)
            self._completion = gtk.Entry.get_completion(self)
            return

        old = self.get_completion()
        if old == completion:
            return completion

        if old and isinstance(old, KiwiEntryCompletion):
            old.disconnect_completion_signals()

        self._completion = completion

        # First, tell the completion what entry it will complete
        completion.set_entry(self)
        completion.set_model(gtk.ListStore(str, object))
        completion.set_text_column(0)
        self.set_exact_completion(False)
        completion.connect("match-selected",
                           self._on_completion__match_selected)
        self._current_object = None
        return completion

    def _completion_exact_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT]
        return key.startswith(content)

    def _completion_normal_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return
        raw_content = model[iter][COL_TEXT]
        if raw_content is not None:
            return key.lower() in raw_content.lower()
        else:
            return False

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        # this updates current_object and triggers content-changed
        self.set_text(model[iter][COL_TEXT])
        self.set_position(-1)
        # FIXME: Enable this at some point
        #self.activate()

    def _appers_later(self, char, start):
        """
        Check if a char appers later on the mask. If it does, return
        the field it appers at. returns False otherwise.
        """
        validators = self._mask_validators
        i = start
        while i < len(validators):
            if self._mask_validators[i] == char:
                field = self._get_field_at_pos(i)
                if field is None:
                    return False

                return field

            i += 1

        return False

    def _can_insert_at_pos(self, new, pos):
        """
        Check if a chararcter can be inserted at some position

        @param new: The char that wants to be inserted.
        @param pos: The position where it wants to be inserted.

        @return: Returns None if it can be inserted. If it cannot be,
                 return the next position where it can be successfuly
                 inserted.
        """
        validators = self._mask_validators

        # Do not let insert if the field is full
        field = self._get_field_at_pos(pos)
        if field is not None:
            text = self.get_field_text(field)
            length = self.get_field_length(field)
            if len(text) == length:
                gtk.gdk.beep()
                return pos

        # If the char confirms to the mask, but is a static char, return the
        # position after that static char.
        if (self._confirms_to_mask(pos, new) and
            not isinstance(validators[pos], int)):
            return pos+1

        # If does not confirms to mask:
        #  - Check if the char the user just tried to enter appers later.
        #  - If it does, Jump to the start of the field after that
        if not self._confirms_to_mask(pos, new):
            field = self._appers_later(new, pos)
            if field is not False:
                pos = self.get_field_pos(field+1)
                if pos is not None:
                    gobject.idle_add(self.set_position, pos)
            return pos

        return None

    def _insert_at_pos(self, text, new, pos):
        """
        Inserts the character at the give position in text. Note that the
        insertion won't be applied to the entry, but to the text provided.

        @param text:    Text that it will be inserted into.
        @param new:     New text to insert.
        @param pos:     Positon to insert at

        @return:    Returns a tuple, with the position after the insetion
                    and the new text.
        """
        field = self._get_field_at_pos(pos)
        length = len(new)
        new_pos = pos
        start, end = self._mask_fields[field]

        # Shift Right
        new_text = (text[:pos] + new +
                    self._shift_text(pos, end, Direction.RIGHT)[1:] +
                    text[end:])

        # Overwrite Right
#        new_text = (text[:pos] + new +
#                    text[pos+length:end]+
#                    text[end:])
        new_pos = pos+1
        gobject.idle_add(self.set_position, new_pos)

        # If the field is full, jump to the next field
        if len(self.get_field_text(field)) == self.get_field_length(field)-1:
            gobject.idle_add(self.set_field, field+1, True)
            self.set_field(field+1)

        return new_pos, new_text

    def _update_position(self):
        if self.get_property('xalign') > 0.5:
            self._icon_pos = gtk.POS_LEFT
        else:
            self._icon_pos = gtk.POS_RIGHT

        # If the text is right to left, we have to use the oposite side
        RTL = gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL
        if RTL:
            if self._icon_pos == gtk.POS_LEFT:
                self._icon_pos = gtk.POS_RIGHT
            else:
                self._icon_pos = gtk.POS_LEFT


    # Callbacks
    def _on_insert_text(self, editable, new, length, position):
        if not self._mask or self._block_insert:
            return
        new = unicode(new)
        pos = self.get_position()

        self.stop_emission('insert-text')

        text = self.get_text()
        # Insert one char at a time
        for c in new:
            _pos = self._can_insert_at_pos(c, pos)
            if _pos is None:
                pos, text = self._insert_at_pos(text, c, pos)
            else:
                pos = _pos

        # Change the text with the new text.
        self._block_changed = True
        self._really_delete_text(0, -1)
        self._block_changed = False

        self._really_insert_text(text, 0)

    def _on_delete_text(self, editable, start, end):
        if not self._mask or self._block_delete:
            return

        self.stop_emission('delete-text')

        pos = self.get_position()
        # Trying to delete an static char. Delete the char before that
        if (0 < start < len(self._mask_validators)
            and not isinstance(self._mask_validators[start], int)
            and pos != start):
            self._on_delete_text(editable, start-1, start)
            return

        # we just tried to delete, stop the selection.
        self._selecting = False

        field = self._get_field_at_pos(end-1)
        # Outside a field. Cannot delete.
        if field is None:
            self.set_position(end-1)
            return
        _start, _end = self._mask_fields[field]

        # Deleting from outside the bounds of the field.
        if start < _start or end > _end:
            _start, _end = start, end

        # Change the text
        text = self.get_text()

        # Shift Left
        new_text = (text[:start] +
                    self._shift_text(start, _end, Direction.LEFT,
                                     end-start) +
                    text[_end:])

        # Overwrite Left
#        empty_mask = self.get_empty_mask()
#        new_text = (text[:_start] +
#                    text[_start:start] +
#                    empty_mask[start:start+(end-start)] +
#                    text[start+(end-start):_end] +
#                    text[_end:])

        new_pos = start

        self._block_changed = True
        self._really_delete_text(0, -1)
        self._block_changed = False
        self._really_insert_text(new_text, 0)

        # Position the cursor on the right place.
        self.set_position(new_pos)
        if pos == new_pos:
            self._handle_position_change()

    def _after_grab_focus(self, widget):
        # The text is selectet in grab-focus, so this needs to be done after
        # that:
        if self.is_empty():
            if self._mask:
                self.set_field(0)
            else:
                self.set_position(0)

    def _on_focus(self, widget, direction):
        if not self._mask:
            return

        field = self._current_field

        if (direction == gtk.DIR_TAB_FORWARD or
            direction == gtk.DIR_DOWN):
            field += 1
        elif (direction == gtk.DIR_TAB_BACKWARD or
              direction == gtk.DIR_UP):
            field = -1

        # Leaving the entry
        if field == len(self._mask_fields) or field == -1:
            self.select_region(0, 0)
            self._current_field = -1
            return False

        if field < 0:
            field = len(self._mask_fields)-1

        # grab_focus changes the selection, so we need to grab_focus before
        # making the selection.
        self.grab_focus()
        self.set_field(field, select=True)

        return True

    def _on_notify_selection_bound(self, widget, pspec):
        if not self._mask:
            return

        if not self.is_focus():
            return

        if self._selecting:
            return

        self._handle_position_change()

    def _on_notify_xalign(self, entry, pspec):
        self._update_position()

    def _handle_position_change(self):
        pos = self.get_position()
        field = self._get_field_at_pos(pos)

        # Humm, the pos is not inside any field. Get the next pos inside
        # some field, depending on the direction that the cursor is
        # moving
        diff = pos - self._pos
        # but move only one position at a time.
        if diff:
            diff /= abs(diff)

        _field = field
        if diff:
            while _field is None and pos >= 0:
                pos += diff
                _field = self._get_field_at_pos(pos)
                self._pos = pos
            if pos < 0:
                self._pos = self.get_field_pos(0)

        if field is None:
            self.set_position(self._pos)
        else:
            if self._current_field != -1:
                self._current_field = field
            self._pos = pos

    def _on_changed(self, widget):
        if self._block_changed:
            self.stop_emission('changed')

    def _on_focus_out_event(self, widget, event):
        if not self._mask:
            return

        self._current_field = -1

    def _on_move_cursor(self, entry, step, count, extend_selection):
        self._selecting = extend_selection

    # Old IconEntry API

    def set_tooltip(self, text):
        if self._icon_pos == gtk.POS_LEFT:
            icon = 'primary-icon-tooltip-text'
        else:
            icon = 'secondary-icon-tooltip-text'
        self.set_property(icon, text)

    def set_pixbuf(self, pixbuf):
        if self._icon_pos == gtk.POS_LEFT:
            icon = 'primary-icon-pixbuf'
        else:
            icon = 'secondary-icon-pixbuf'
        self.set_property(icon, pixbuf)

    def update_background(self, color):
        self.modify_base(gtk.STATE_NORMAL, color)

    def get_background(self):
        return self.style.base[gtk.STATE_NORMAL]

    # IComboMixin

    def prefill(self, itemdata, sort=False):
        """
        See L{kiwi.interfaces.IEasyCombo.prefill}
        """

        if not isinstance(itemdata, (list, tuple)):
            raise TypeError("'data' parameter must be a list or tuple of item "
                            "descriptions, found %s") % type(itemdata)

        completion = self._get_entry_completion()
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

        values = set()
        if mode == ENTRY_MODE_TEXT:
            if sort:
                itemdata.sort()

            for item in itemdata:
                if item in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%r into the entry" % item)
                else:
                    values.add(item)

                model.append((item, None))
        elif mode == ENTRY_MODE_DATA:
            if sort:
                itemdata.sort(lambda x, y: cmp(x[0], y[0]))

            for item in itemdata:
                text, data = item
                # Add (n) to the end in case of duplicates
                count = 1
                orig = text
                while text in values:
                    text = orig + ' (%d)' % count
                    count += 1

                values.add(text)
                model.append((text, data))
        else:
            raise TypeError("Incorrect format for itemdata; see "
                            "docstring for more information")

    def get_iter_by_data(self, data):
        if self._mode != ENTRY_MODE_DATA:
            raise TypeError(
                "select_item_by_data can only be used in data mode")

        completion = self._get_entry_completion()
        model = completion.get_model()

        for row in model:
            if row[COL_OBJECT] == data:
                return row.iter
                break
        else:
            raise KeyError("No item correspond to data %r in the combo %s"
                           % (data, self.name))

    def get_iter_by_label(self, label):
        completion = self._get_entry_completion()
        model = completion.get_model()
        for row in model:
            if row[COL_TEXT] == label:
                return row.iter
        else:
            raise KeyError("No item correspond to label %r in the combo %s"
                           % (label, self.name))

    def get_selected_by_iter(self, treeiter):
        completion = self._get_entry_completion()
        model = completion.get_model()
        mode = self._mode
        text = model[treeiter][COL_TEXT]
        if text != self.get_text():
            return

        if mode == ENTRY_MODE_TEXT:
            return text
        elif mode == ENTRY_MODE_DATA:
            return model[treeiter][COL_OBJECT]
        else:
            raise AssertionError

    def get_selected_label(self, treeiter):
        completion = self._get_entry_completion()
        model = completion.get_model()
        return model[treeiter][COL_TEXT]

    def get_selected_data(self, treeiter):
        completion = self._get_entry_completion()
        model = completion.get_model()
        return model[treeiter][COL_OBJECT]

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

    def get_mode(self):
        return self._mode

type_register(KiwiEntry)

def main(args):
    win = gtk.Window()
    win.set_title('gtk.Entry subclass')
    def cb(window, event):
        print 'fields', widget.get_field_text()
        gtk.main_quit()
    win.connect('delete-event', cb)

    widget = KiwiEntry()
    widget.set_mask('000.000.000.000')

    win.add(widget)

    win.show_all()

    widget.select_region(0, 0)
    gtk.main()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
