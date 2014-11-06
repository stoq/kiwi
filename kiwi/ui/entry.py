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
#            Thiago Bellini <hackedbellini@async.com.br>
#

"""
An enchanced version of GtkEntry that supports icons and masks
"""

import gettext
import re
import string
try:
    set
except NameError:
    from sets import Set as set

import gobject
import pango
import gtk

from kiwi.enums import Direction
from kiwi.python import strip_accents
from kiwi.ui.entrycompletion import KiwiEntryCompletion
from kiwi.utils import type_register


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

INPUT_CHAR_MAP = {
    INPUT_ASCII_LETTER: lambda text: text in string.ascii_letters,
    INPUT_ALPHA: unicode.isalpha,
    INPUT_ALPHANUMERIC: unicode.isalnum,
    INPUT_DIGIT: unicode.isdigit,
}


(COL_TEXT,
 COL_OBJECT) = range(2)

# FIXME: Remove this and replace with data_type str/objec
(ENTRY_MODE_UNKNOWN,
 ENTRY_MODE_TEXT,
 ENTRY_MODE_DATA) = range(3)

_ = lambda msg: gettext.dgettext('kiwi', msg)


class KiwiEntry(gtk.Entry):
    """
    The KiwiEntry is a Entry subclass with the following additions:

      - Mask, force the input to meet certain requirements
      - IComboMixin: Allows you work with objects instead of strings
        Adds a number of convenience methods such as :class:`prefill`().

    Properties
    ==========
      - B{completion_ignore_case}: bool
        - if when doing the completion, we should search for a pattern
          ignoring case. Default: True
      - B{completion_ignore_accents}: bool
        - if when doing the completion, we should search for a pattern
          ignoring string accents. Default: True
      - B{completion_hightlight_match}: bool
        - if when doing the completion, the pattern should be
          highlighted in bold. Default: True
    """
    __gtype_name__ = 'KiwiEntry'

    completion_ignore_case = gobject.property(type=bool, default=True)
    completion_ignore_accents = gobject.property(type=bool, default=True)
    completion_hightlight_match = gobject.property(type=bool, default=True)

    def __init__(self):
        self._completion = None

        gtk.Entry.__init__(self)
        self._update_position()
        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)
        self.connect('changed', self._on_changed)
        self.connect('move-cursor', self._on_move_cursor)

        # Ideally, this should be connected to notify::cursor-position, but
        # there seems to be a bug in gtk that the notification is not emited
        # when it should.
        # TODO: investigate that and report a bug.
        self.connect('notify::selection-bound',
                     self._on_notify_selection_bound)
        self.connect('notify::xalign', self._on_notify_xalign)

        self.set_property("truncate-multiline", True)

        self._block_changed = False

        self._current_object = None
        self._mode = ENTRY_MODE_TEXT

        self._exact_completion = True
        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        self._keep_next_position = False
        self._pos = None
        self._selecting = False
        self._block_insert = False
        self._block_delete = False

        # This are used to cache the data from the completion match funcions.
        # The first time the completion is executed it doesnt make any
        # difference, but for subsequent completions it improves considerably
        self._last_key = None
        self._fixed_key = None
        self._cache = {}

    # Properties

    def _get_mask(self):
        return self._mask

    def _set_mask(self, value):
        try:
            self.set_mask(value)
            return self.get_mask()
        except MaskError:
            pass

    mask = gobject.property(getter=_get_mask,
                            setter=_set_mask,
                            type=str, default='')

    # Public API

    def set_text(self, text):
        completion = self.get_completion()

        if isinstance(completion, KiwiEntryCompletion):
            self.handler_block(completion.changed_id)

        if self._mask:
            # When using masks, let our _on_insert_text and _on_delete_text
            # take care of things. They will do it right!
            self.delete_text(0, -1)
            self.insert_text(text, 0)
        else:
            gtk.Entry.set_text(self, text)

        if isinstance(completion, KiwiEntryCompletion):
            self.handler_unblock(completion.changed_id)

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
        U{http://tinyurl.com/one6c6r}

        Example mask for a ISO-8601 date::

            >>> entry = KiwiEntry()
            >>> entry.set_mask('0000-00-00')

        :param mask: the mask to set
        """
        if not mask:
            self.modify_font(pango.FontDescription("sans"))
            self._mask = mask
            return

        # First, reset
        self._mask_validators = []

        for i, c in enumerate(unicode(mask)):
            if c in INPUT_FORMATS:
                self._mask_validators += [INPUT_FORMATS[c]]
            else:
                self._mask_validators.append(c)

        self.modify_font(pango.FontDescription("monospace"))

        self._really_delete_text(0, -1)
        self._mask = mask
        self._really_insert_text(self.get_empty_mask(), 0)

        self._handle_position_change()

    def get_mask(self):
        """
        Get the mask.
        :returns: the mask
        """
        return self._mask

    def get_empty_mask(self, start=None, end=None):
        """
        Gets the empty mask between start and end

        :param start:
        :param end:
        :returns: mask
        :rtype: string
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

    def set_exact_completion(self):
        """Enable exact entry completion.

        Exact means it will match from the beggining of the string.
        """
        self._exact_completion = True
        completion = self._get_entry_completion()
        completion.set_match_func(self._completion_exact_match_func)

    def set_normal_completion(self):
        """Enable normal entry completion.

        Normal means it will match anywhere on the string.
        """
        self._exact_completion = False
        completion = self._get_entry_completion()
        completion.set_match_func(self._completion_normal_match_func)

    def get_current_object(self):
        """Returns the current object on this entry

        Note that this is only valid if the mode set here is
        :mod:`.ENTRY_MODE_DATA`. At any other mode, this will
        return ``None``.

        :returns: the current object matched by the text entry.
            ``None`` means the text didn't match any object.
        """
        if self._mode != ENTRY_MODE_DATA:
            return None
        return self._current_object

    def is_empty(self):
        text = self.get_text()
        if self._mask:
            empty = self.get_empty_mask()
        else:
            empty = ''

        return text == empty

    # Private

    def _get_next_non_static_char_pos(self, pos, direction=Direction.LEFT):
        text = unicode(self.get_text())

        pos = pos + direction
        while 0 <= pos < len(text):
            char = text[pos]
            validator = self._mask_validators[pos]

            if isinstance(validator, int) and INPUT_CHAR_MAP[validator](char):
                return pos

            pos += direction

        return None

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

    def _insert_char_at_position(self, pos, char):
        text = unicode(self.get_text())
        if pos >= len(text):
            return
        validator = self._mask_validators[pos]

        if isinstance(validator, unicode) and char == validator:
            # Trying to insert the same static char. Nothing to do, but return
            # pos to avoid the callsite thinking it was an error
            return pos
        elif isinstance(validator, unicode):
            # This is a static char. Try to insert the char on next pos
            return self._insert_char_at_position(pos + 1, char)
        elif isinstance(validator, int) and INPUT_CHAR_MAP[validator](char):
            old_char = text[pos]
            # We cannot shift an existing char if there's no space left
            if (old_char != ' ' and
                    text.count(' ') - self._mask_validators.count(' ') == 0):
                return

            self._block_changed = True
            self._really_delete_text(pos, pos + 1)
            self._block_changed = False

            self._really_insert_text(char, pos)

            # If the old char was a valid one, shift it to the right. The
            # validation and shifting will be done recursively
            if old_char != ' ':
                self._insert_char_at_position(pos + 1, old_char)

            return pos

    def _delete_char_at_position(self, pos):
        text = unicode(self.get_text())
        char = text[pos]
        validator = self._mask_validators[pos]
        assert 0 <= pos < len(text)

        if char == ' ':
            # Already removed
            pass
        elif isinstance(validator, unicode):
            # We will not remove static chars so try to remove the next one.
            # The callsite should handle to case where the char to remove is
            # the previous one. We don't do it here to keep the recursion simple
            pos += 1
            if 0 <= pos < len(text):
                self._delete_char_at_position(pos)
        elif isinstance(validator, int):
            next_char_pos = self._get_next_non_static_char_pos(pos)
            if next_char_pos is None:
                next_char = None
            else:
                next_char = unicode(text[next_char_pos])

            self._block_changed = True
            self._really_delete_text(pos, pos + 1)
            self._block_changed = False

            # If next char is valid, shift it to the left. This will be done
            # recursively as needed
            if next_char is None or next_char == ' ':
                self._really_insert_text(' ', pos)
            else:
                self._really_insert_text(next_char, pos)
                self._delete_char_at_position(next_char_pos)
        else:
            raise AssertionError

    def _update_current_object(self, text):
        if self._mode != ENTRY_MODE_DATA:
            return

        self._current_object = None
        for row in self.get_completion().get_model():
            if row[COL_TEXT] == text:
                self._current_object = row[COL_OBJECT]
                break

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
        if isinstance(completion, KiwiEntryCompletion):
            old = self.get_completion()
            if old == completion:
                return completion

            if old and isinstance(old, KiwiEntryCompletion):
                old.disconnect_completion_signals()

            completion.set_entry(self)
            completion.connect("match-selected",
                               self._on_completion__match_selected)
        else:
            gtk.Entry.set_completion(self, completion)

        self._completion = completion
        completion.set_model(gtk.ListStore(str, object))
        completion.set_text_column(0)

        if self._exact_completion:
            self.set_exact_completion()
        else:
            self.set_normal_completion()

        completion.set_cell_data_func(completion.get_cells()[0],
                                      self._completion_cell_data_func)
        self._current_object = None

        return completion

    def _completion_cell_data_func(self, completion, cell, model, iter_):
        if not self.completion_hightlight_match:
            return

        text = unicode(model[iter_][COL_TEXT])
        search_str = unicode(self.get_text())

        if self._exact_completion:
            markup = '<b>%s</b>%s' % (text[:len(search_str)],
                                      text[len(search_str):])
        else:
            # This will replace search_str to <b>search_str</b> on text
            # ignoring case. Like, 'Ball' will replace both 'Ball' and 'ball'
            # to <b>Ball</b> and <b>ball</b> accordingly.
            markup = re.sub('(%s)' % search_str, '<b>\\1</b>', text,
                            flags=re.IGNORECASE)

        cell.props.markup = markup.encode('utf-8')

    def _get_key_for_completion(self, key):
        if key == self._last_key:
            return self._fixed_key

        self._last_key = key
        # We need to do strip_accents() before lower(), since
        # lower() on win32 will corrupt the utf-8 encoded string
        if self.completion_ignore_accents:
            key = strip_accents(key)
        if self.completion_ignore_case:
            key = key.lower()

        self._fixed_key = key
        return self._fixed_key

    def _get_content_for_completion(self, model, iter):
        content = model[iter][COL_TEXT]
        hit = self._cache.get(content)
        if hit or content is None:
            return hit

        fixed = content
        # We need to do strip_accents() before lower(), since
        # lower() on win32 will corrupt the utf-8 encoded string
        if self.completion_ignore_accents:
            fixed = strip_accents(fixed)
        if self.completion_ignore_case:
            fixed = fixed.lower()
        self._cache[content] = fixed
        return fixed

    def _completion_exact_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return False

        content = self._get_content_for_completion(model, iter)
        if content is None:
            # FIXME: Find out why this happens some times
            return False

        key = self._get_key_for_completion(key)
        return content.startswith(key)

    def _completion_normal_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return False

        content = self._get_content_for_completion(model, iter)
        if content is None:
            # FIXME: Find out why this happens some times
            return False

        key = self._get_key_for_completion(key)
        return key in content

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        # this updates current_object and triggers content-changed
        self.set_text(model[iter][COL_TEXT])
        self.set_position(-1)
        # FIXME: Enable this at some point
        #self.activate()

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

        self.stop_emission('insert-text')

        text = self.get_text()
        pos = self.get_position()

        # self.set_text('') will fall into this
        if not len(new):
            return

        # If the first char on the mask is static and someone is trying to
        # insert it again (via set_text, ctrl+v, etc), remove it or it will
        # conflict with our optimization on _handle_position_change that
        # doesn't allow the position to be on 0 on and mess things here
        if self.is_empty() and pos != 0 and not self._selecting:
            for pos_ in xrange(0, len(text)):
                validator = self._mask_validators[pos_]
                if isinstance(validator, unicode) and new[0] == validator:
                    new = new[1:]
                else:
                    break
        else:
            pos = self.get_position()

        if pos >= len(text):
            gtk.gdk.beep()
            return

        for c in unicode(new):
            pos = self._insert_char_at_position(pos, c)
            # If pos is None, the char is not valid. When typing, it will just
            # beep. When pasting something like 'vviv' (v for valid i for
            # invalid), it will insert vv and stop after that, beeping.
            # We cannot simply skip it as the order of a string matters
            if pos is None:
                gtk.gdk.beep()
                return
            pos += 1

        # If the last char was inserted at a static char position (and thus,
        # it was really inserted at that pos + 1), put the cursor after that
        while pos < len(text):
            validator = self._mask_validators[pos]
            if not isinstance(validator, unicode):
                break
            pos += 1

        # FIXME: gtk_entry.c sends the position arg as a pointer to call
        # set_position later. We cannot modify the pointed value from here.
        # Because of that, after this another call to set_position will be
        # made to set the cursor on the pointed value that didn't change,
        # so we just need to ignore that second call.
        self._pos = None
        self._keep_next_position = True
        self.set_position(pos)

        # This is a specific workaround to when text is pasted in the entry.
        # When that happens, the call to set_position above will not notify
        # cursor-position neither selectiuon-bound and thus,
        # self._handle_position_change will not be called. By calling it by
        # hand we will be sure that it will keep next position the right way
        if self._pos is None:
            self._handle_position_change()

    def _on_delete_text(self, editable, start, end):
        if not self._mask or self._block_delete:
            return

        self.stop_emission('delete-text')

        if end == -1:
            end = len(self.get_text())

        # When deleting with backspace just after a static char, we
        # should delete the char before it. This is the only case that
        # _delete_char_at_position will not handle for us
        if end - start == 1 and not self._selecting:
            for pos in reversed(xrange(0, self.get_position() + 1)):
                validator = self._mask_validators[start]
                if isinstance(validator, unicode) or validator == ' ':
                    start -= 1
                    end -= 1
                else:
                    break
        else:
            pos = self.get_position()

        # This will happen if there was a static char at the beggining and
        # someone pressed backspace on it. Nothing to do
        if start < 0:
            gtk.gdk.beep()
            return

        for pos in reversed(xrange(start, end)):
            validator = self._mask_validators[pos]
            # Only delete the char if it's not a static char. Since we are
            # threating the case where we are pressing del/backspace on that
            # char above, this is for sure a selection deletion.
            if isinstance(validator, unicode):
                continue
            self._delete_char_at_position(pos)

        # we just tried to delete, stop the selection.
        self._selecting = False
        self.set_position(start)

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
        actual_pos = self.get_position()
        text = self.get_text()

        # A simple optimization: If the first char(s) are static, put the
        # cursor after it to make it look nicer
        if actual_pos == 0 and isinstance(self._mask_validators[0], unicode):
            for pos in xrange(0, len(self._mask_validators)):
                if not isinstance(self._mask_validators[pos], unicode):
                    self.set_position(pos)
                    return

        for pos, c in enumerate(unicode(text)):
            validator = self._mask_validators[pos]
            if isinstance(validator, int) and c == ' ':
                break
        else:
            pos = None

        # Take a look on _on_insert_text to see why this is needed
        if self._keep_next_position and self._pos is not None:
            self.set_position(self._pos)
            self._keep_next_position = False
            self._pos = None
        elif pos is not None and pos < actual_pos:
            self.set_position(pos)
            actual_pos = pos

        # Take a look on _on_insert_text to see why this is needed
        if self._keep_next_position:
            self._pos = actual_pos

    def _on_changed(self, widget):
        if self._block_changed:
            self.stop_emission('changed')
        self._update_current_object(widget.get_text())

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
        See :class:`kiwi.interfaces.IEasyCombo.prefill`
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

    def set_mode(self, mode):
        """Set the entry mode

        Use this if you need to set mode by hand for some reason,
        but usually there's no reason to do so since the text mode is
        set by default and updated to data mode if the entry gets prefilled

        :param mode: one of :mod:`ENTRY_MODE_TEXT` or :mod:`ENTRY_MODE_DATA`
        """
        if mode not in [ENTRY_MODE_TEXT, ENTRY_MODE_DATA]:
            raise TypeError("mode should be ENTRY_MODE_TEXT or "
                            "ENTRY_MODE_DATA, got %r" % (mode, ))
        self._mode = mode

    def get_mode(self):
        """Returns the actual entry mode

        :returns: one of :mod:`ENTRY_MODE_TEXT` or :mod:`ENTRY_MODE_DATA`
        """
        return self._mode

type_register(KiwiEntry)


if __name__ == '__main__':
    win = gtk.Window()
    win.set_title('gtk.Entry subclass')

    def cb(window, event):
        gtk.main_quit()
    win.connect('delete-event', cb)

    widget = KiwiEntry()
    #widget.set_mask('000.000.000.000')
    widget.set_mask('(00) 0000-0000')

    win.add(widget)

    win.show_all()

    widget.select_region(0, 0)
    gtk.main()
