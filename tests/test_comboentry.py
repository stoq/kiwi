import unittest

import gtk

from kiwi.enums import ComboMode
from kiwi.ui.comboentry import ComboEntry
from kiwi.ui.widgets.combo import ProxyComboEntry

class TestComboEntry(unittest.TestCase):
    def setUp(self):
        self.called = False

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

    def _on_activate(self, combo):
        self.called = True

    def testActivate(self):
        entry = ComboEntry()
        entry.connect('activate', self._on_activate)
        entry.entry.emit('activate')
        self.assertEqual(self.called, True)

class TestProxyComboEntry(unittest.TestCase):
    def testSelectItemByLabel(self):
        entry = ProxyComboEntry()
        entry.prefill(['one', 'two'])
        entry.select_item_by_label('one')
        self.assertEqual(entry.get_text(), 'one')
        entry.select_item_by_label('two')
        self.assertEqual(entry.get_text(), 'two')
        self.assertRaises(KeyError, entry.select_item_by_label, 'three')

    def testSelectItemByLabelInDataMode(self):
        entry = ProxyComboEntry()
        entry.prefill([('one', 1), ('two', 2)])
        entry.select_item_by_label('one')
        self.assertEqual(entry.get_text(), 'one')
        entry.select_item_by_label('two')
        self.assertEqual(entry.get_text(), 'two')
        self.assertRaises(KeyError, entry.select_item_by_label, 'three')

    def testSelectItemByData(self):
        entry = ProxyComboEntry()
        entry.prefill([('one', 1), ('two', 2)])
        entry.select_item_by_data(1)
        self.assertEqual(entry.get_text(), 'one')
        entry.select_item_by_data(2)
        self.assertEqual(entry.get_text(), 'two')
        self.assertRaises(KeyError, entry.select_item_by_data, 3)

    def testSelectItemByDataInTextMode(self):
        entry = ProxyComboEntry()
        entry.prefill(['one', 'two'])
        self.assertRaises(TypeError, entry.select_item_by_data, 1)

    def testGetSelectedInTextMode(self):
        entry = ProxyComboEntry()
        self.assertEqual(entry.get_selected(), None)
        entry.prefill(['one', 'two'])
        entry.select_item_by_label('two')
        self.assertEqual(entry.get_selected(), 'two')

    def testGetSelectedInDataMode(self):
        entry = ProxyComboEntry()
        self.assertEqual(entry.get_selected(), None)
        entry.prefill([('one', 1), ('two', 2)])
        entry.select_item_by_label('two')
        self.assertEqual(entry.get_selected(), 2)

    def testSelectInTextMode(self):
        entry = ProxyComboEntry()
        entry.prefill(['one', 'two'])
        entry.select('two')
        self.assertEqual(entry.get_selected(), 'two')

    def testSelectInDataMode(self):
        entry = ProxyComboEntry()
        entry.prefill([('one', 1), ('two', 2)])
        entry.select(2)
        self.assertEqual(entry.get_selected(), 2)

    def testDataMode(self):
        entry = ProxyComboEntry()
        self.assertEqual(entry.get_mode(), ComboMode.UNKNOWN)
        entry.prefill([('one', 1), ('two', 2)])
        self.assertEqual(entry.get_mode(), ComboMode.DATA)

    def testStringMode(self):
        entry = ProxyComboEntry()
        self.assertEqual(entry.get_mode(), ComboMode.UNKNOWN)
        entry.prefill(['one', 'two'])
        self.assertEqual(entry.get_mode(),  ComboMode.STRING)

if __name__ == '__main__':
    unittest.main()
