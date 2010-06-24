from twisted.trial import unittest
from utils import refresh_gui

import gtk
from gtk import keysyms

from kiwi.ui.delegates import Delegate
from kiwi.ui.entry import KiwiEntry

SPECIAL_KEYS = {
    '/' : 'slash',
    '+' : 'plus',
    '-' : 'minus',
    '(' : 'parenleft',
    ')' : 'parenright',
    ' ' : 'space',
}

DELAY = 0.1

def send_backspace(widget):
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysyms.BackSpace)
    event.hardware_keycode = 22
    event.window = widget.window
#    widget.event(event)
    gtk.main_do_event(event)
    refresh_gui(DELAY)

def send_delete(widget):
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysyms.Delete)
    event.hardware_keycode = 107
    event.window = widget.window
    gtk.main_do_event(event)
#    widget.event(event)
    refresh_gui(DELAY)


def send_key(widget, key):
    if isinstance(key, str) and key.isdigit():
        key = 'KP_'+key
    elif isinstance(key, str) and key in SPECIAL_KEYS:
        key = SPECIAL_KEYS[key]

    keysym  = getattr(keysyms, key)

    # Key press
    event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
    event.keyval = int(keysym)
    event.window = widget.window
    widget.event(event)

    refresh_gui(DELAY)

def insert_text(widget, text):
    for i in text:
        send_key(widget, i)

LEFT, RIGHT = -1, 1
def move(entry, direction):
    entry.emit('move-cursor', gtk.MOVEMENT_VISUAL_POSITIONS, direction, False)

def select(entry, start, end):
    entry.set_position(start)
    entry.emit('move-cursor', gtk.MOVEMENT_VISUAL_POSITIONS, end-start, True)


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
        insert_text(entry, '1/2/3333')
        self.assertEqual(entry.get_text(), '1 /2 /3333')

        entry.set_mask('(00) 0000-0000')
        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        refresh_gui(DELAY)
        insert_text(entry, '1234567890')
        self.assertEqual(entry.get_text(), '(12) 3456-7890')


    def testMovementTabsEmptyMask(self):
        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        self.assertEqual(entry.get_field(), None)

        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        self.assertEqual(entry.get_field(), 0)

        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        self.assertEqual(entry.get_field(), 1)

        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        self.assertEqual(entry.get_field(), 2)

        entry.emit('focus', gtk.DIR_TAB_FORWARD)
        self.assertEqual(entry.get_field(), None)

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
        self.assertEqual(entry.get_position(), 2)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 3)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 5)

        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 3)


        # Home
        entry.emit('move-cursor', gtk.MOVEMENT_DISPLAY_LINE_ENDS, -1, False)
        self.assertEqual(entry.get_position(), 1)

        # End
        entry.emit('move-cursor', gtk.MOVEMENT_DISPLAY_LINE_ENDS, 1, False)
        self.assertEqual(entry.get_position(), 14)

    def testInsertAndMovementKeys(self):
        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1')
        self.assertEqual(entry.get_text(), '(1 )     -    ')

        move(entry, LEFT)
        self.assertEqual(entry.get_position(), 1)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 2)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 3)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 5)

        insert_text(entry, '2')
        self.assertEqual(entry.get_text(), '(1 ) 2   -    ')

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 7)

        insert_text(entry, '3')
        self.assertEqual(entry.get_text(), '(1 ) 2 3 -    ')

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 9)

        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 10)

        insert_text(entry, '4')
        self.assertEqual(entry.get_text(), '(1 ) 2 3 -4   ')


    # FIXME: Delete/Backspace does not work on windows or xvfb
    def testBackspace(self):
        if 1:
            return

        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1234')
        refresh_gui(DELAY)
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
        if 1:
            return

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
        self.assertEqual(entry.get_text(), '(2 ) 3456-78  ')

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  ) 3456-78  ')

        move(entry, RIGHT)
        move(entry, RIGHT)
        move(entry, RIGHT)
        move(entry, RIGHT)
        self.assertEqual(entry.get_position(), 6)

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  ) 356 -78  ')

        send_delete(entry)
        refresh_gui(DELAY)
        self.assertEqual(entry.get_text(), '(  ) 36  -78  ')

    def testDeleteSelection(self):
        if 1:
            return

        entry = self.entry
        entry.set_mask('(00) 0000-0000')
        entry.grab_focus()

        insert_text(entry, '1')
        self.assertEqual(entry.get_text(), '(1 )     -    ')

        select(entry, 2, 0)
        send_delete(entry)
        self.assertEqual(entry.get_position(), 1)

        insert_text(entry, '1234')
        self.assertEqual(entry.get_text(), '(12) 34  -    ')

        select(entry, 2, 0)
        refresh_gui(2)
        send_delete(entry)
        refresh_gui(2)
        self.assertEqual(entry.get_position(), 1)


if __name__ == '__main__':
    unittest.main()

