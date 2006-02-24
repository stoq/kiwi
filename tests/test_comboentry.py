import unittest

import gtk

from kiwi.ui.comboentry import ComboEntry
from kiwi.ui.widgets.combo import ProxyComboEntry

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

class TestProxyComboEntry(unittest.TestCase):
    def testSelectItemByData(self):
        entry = ProxyComboEntry()
        entry.prefill([('one', 1), ('two', 2)])
        entry.select_item_by_data(1)
        self.assertEqual(entry.get_text(), 'one')
        entry.select_item_by_data(2)
        self.assertEqual(entry.get_text(), 'two')

if __name__ == '__main__':
    unittest.main()
