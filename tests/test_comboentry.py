import unittest

import gtk

from kiwi.ui.comboentry import ComboEntry

class TestComboEntry(unittest.TestCase):
    def testSimple(self):
        entry = ComboEntry()
        self.failUnless(isinstance(entry, ComboEntry))

    def testPopup(self):
        entry = ComboEntry()
        win = gtk.Window()
        win.add(entry)
        win.show_all()
        entry.hide()
        entry.popup()
        entry.popdown()

if __name__ == '__main__':
    unittest.main()
