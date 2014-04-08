import sys
import unittest

import gtk
from gtk import keysyms
from nose.exc import SkipTest
from utils import refresh_gui

from kiwi.ui.delegates import Delegate
from kiwi.ui.entry import KiwiEntry

SPECIAL_KEYS = {
    '/': 'slash',
    '+': 'plus',
    '-': 'minus',
    '(': 'parenleft',
    ')': 'parenright',
    ' ': 'space',
}

# FIXME: Even though we are calling refresh_gui(DELAY), when running a single
# test on a powerful machine, this can return before the event is emitted
# (tested by putting a print on the 'insert-text' callback and not seeing when
# tests were executed very fast, but all otherwise). It's not obvious because
# it _never_ happens when running the whole test suit.
DELAY = 0.1


def send_backspace(widget):
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysyms.BackSpace)
    event.hardware_keycode = 22
    event.window = widget.window
    widget.event(event)
    refresh_gui(DELAY)


def send_delete(widget):
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysyms.Delete)
    event.hardware_keycode = 119
    event.window = widget.window
    widget.event(event)
    refresh_gui(DELAY)


def send_key(widget, key):
    if isinstance(key, str) and key.isdigit():
        key = 'KP_' + key
    elif isinstance(key, str) and key in SPECIAL_KEYS:
        key = SPECIAL_KEYS[key]

    keysym = getattr(keysyms, key)

    # Key press
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysym)
    event.window = widget.window
    widget.event(event)

    refresh_gui(DELAY)


def insert_text(widget, text):
    for i in text:
        send_key(widget, i)

    refresh_gui(DELAY)


LEFT, RIGHT = -1, 1


def move(entry, direction):
    entry.emit('move-cursor', gtk.MOVEMENT_VISUAL_POSITIONS, direction, False)


def select(entry, start, end):
    entry.set_position(start)
    entry.emit('move-cursor', gtk.MOVEMENT_VISUAL_POSITIONS, end - start, True)


class MasksDelegate(Delegate):
    def __init__(self):
        self.win = gtk.Window()
        self.entry = KiwiEntry()
        self.win.add(self.entry)

        Delegate.__init__(self, toplevel=self.win)
        self.win.show_all()


class TestMasks(unittest.TestCase):
    def setUp(self):
        self.delegate = MasksDelegate()
        self.entry = self.delegate.entry

    def tearDown(self):
        self.delegate.win.destroy()

    def testSetMask(self):
        entry = self.entry
        entry.set_mask('00/00/0000')
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '  /  /    ')

        entry.set_mask('(00) 0000-0000')
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  )     -    ')

    def testSetText(self):
        entry = self.entry
        entry.set_mask('00/00/0000')
        refresh_gui(DELAY)
        entry.set_text('12/34/5678')
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '12/34/5678')

        entry.set_mask('(00) 0000-0000')
        refresh_gui(DELAY)
        entry.set_text('(11) 1234-5678')
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(11) 1234-5678')

        entry.set_text('')
        self.assertEqual(entry.get_text(), entry.get_empty_mask())

    def testInserting(self):
        entry = self.entry
        entry.set_mask('00/00/0000')
        entry.grab_focus()
        insert_text(entry, '12345678')
        self.assertEqual(entry.get_text(), '12/34/5678')

        entry.set_text('')
        insert_text(entry, '12/34/5678')
        self.assertEqual(entry.get_text(), '12/34/5678')

        entry.set_text('')
        insert_text(entry, '1234')
        self.assertEqual(entry.get_text(), '12/34/    ')

        entry.set_mask('(00) 0000-0000')
        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        refresh_gui(DELAY)
        insert_text(entry, '1234567890')
        self.assertEqual(entry.get_text(), '(12) 3456-7890')

    def testMovementKeysEmptyMask(self):
        entry = self.entry
        entry.set_mask('(00) 0000-0000')

        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        refresh_gui(DELAY)

        self.assertEqual(entry.get_position(), 1)

        # Left
        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 1)

        # Right
        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 1)

        # Home
        entry.emit('move-cursor', gtk.MOVEMENT_DISPLAY_LINE_ENDS, -1, False)
        self.assertEqual(entry.get_position(), 1)

        # End
        entry.emit('move-cursor', gtk.MOVEMENT_DISPLAY_LINE_ENDS, 1, False)
        self.assertEqual(entry.get_position(), 1)

    def testInsertAndMovementKeys(self):
        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1')
        self.assertEqual(entry.get_text(), '(1 )     -    ')
        self.assertEqual(entry.get_position(), 2)

        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 1)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 2)

        # Can't enter an empty field
        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 2)

        insert_text(entry, '2')
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(12)     -    ')
        # The position should be after the space in the mask
        self.assertEqual(entry.get_position(), 5)

        # Can't enter an empty field
        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 5)

        # But we can move to the space in the mask
        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 4)

        # But trying to insert on it should insert after the space
        insert_text(entry, '9')
        self.assertEqual(entry.get_text(), '(12) 9   -    ')
        self.assertEqual(entry.get_position(), 6)

        # Even after moving to the static field ')'
        move(entry, LEFT)
        move(entry, LEFT)
        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 3)
        insert_text(entry, '8')
        self.assertEqual(entry.get_text(), '(12) 89  -    ')
        self.assertEqual(entry.get_position(), 6)

        insert_text(entry, '345')
        self.assertEqual(entry.get_text(), '(12) 8345-9   ')

    def testBackspace(self):
        if sys.platform == 'win32':
            raise SkipTest("Not supported on windows")

        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1234')
        self.assertEqual(entry.get_text(), '(12) 34  -    ')

        send_backspace(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(12) 3   -    ')

        send_backspace(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(12)     -    ')

        send_backspace(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(1 )     -    ')

        send_backspace(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  )     -    ')
        self.assertEqual(entry.get_position(), 1)

        send_backspace(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  )     -    ')
        self.assertEqual(entry.get_position(), 1)

    def testDelete(self):
        if sys.platform == 'win32':
            raise SkipTest("Not supported on windows")

        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '12345678')
        self.assertEqual(entry.get_text(), '(12) 3456-78  ')

        # Home
        entry.emit('move-cursor', gtk.MOVEMENT_DISPLAY_LINE_ENDS, -1, False)
        self.assertEqual(entry.get_position(), 1)

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(23) 4567-8   ')

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(34) 5678-    ')

        move(entry, RIGHT)
        move(entry, RIGHT)
        move(entry, RIGHT)
        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 5)

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(34) 678 -    ')

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(34) 78  -    ')

    def testDeleteSelection(self):
        if sys.platform == 'win32':
            raise SkipTest("Not supported on windows")

        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1')
        self.assertEqual(entry.get_text(), '(1 )     -    ')

        select(entry, 2, 0)
        refresh_gui(DELAY)
        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_position(), 1)

        insert_text(entry, '1234')
        self.assertEqual(entry.get_text(), '(12) 34  -    ')

        select(entry, 2, 0)
        refresh_gui(DELAY)
        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_position(), 1)


if __name__ == '__main__':
    unittest.main()
