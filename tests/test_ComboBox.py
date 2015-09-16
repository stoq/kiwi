#!/usr/bin/env python
import unittest

from kiwi.python import disabledeprecationcall, Settable
from kiwi.ui.proxy import Proxy
from kiwi.ui.widgets.combo import ProxyComboBox, ProxyComboEntry


class TestComboBox(unittest.TestCase):
    def setUp(self):
        self.combo = ProxyComboBox()

    def _prefill(self):
        self.combo.prefill((('Johan', 1981),
                            ('Lorenzo', 1979),
                            ('Christian', 1976)))

    def testPrefill(self):
        self.combo.prefill(('foo', 'bar'))
        model = self.combo.get_model()
        self.assertEqual(tuple(model[0]), ('foo', None))
        self.assertEqual(tuple(model[1]), ('bar', None))

    def testPrefillWithData(self):
        self.combo.prefill((('foo', 42), ('bar', 138)))
        model = self.combo.get_model()
        self.assertEqual(tuple(model[0]), ('foo', 42))
        self.assertEqual(tuple(model[1]), ('bar', 138))
        self.combo.prefill([])
        self.assertEqual(len(self.combo.get_model()), 0)
        self.assertEqual(len(model), 0)
        self.assertEqual(len(self.combo), 0)

    def testSelectItemByPosition(self):
        self._prefill()
        self.combo.select_item_by_position(1)
        model = self.combo.get_model()
        iter = self.combo.get_active_iter()
        self.assertEqual(model.get_value(iter, 0), 'Lorenzo')
        self.assertEqual(model.get_value(iter, 1), 1979)
        self.assertRaises(KeyError, self.combo.select_item_by_label, 4)

    def testSelectItemByLabel(self):
        self._prefill()
        self.combo.select_item_by_label('Christian')
        model = self.combo.get_model()
        iter = self.combo.get_active_iter()
        rowNo = model.get_path(iter)[0]
        self.assertEqual(rowNo, 2)
        self.assertRaises(KeyError, self.combo.select_item_by_label, 'Salgado')

    def testSelectByData(self):
        self._prefill()
        self.combo.select_item_by_data(1976)
        model = self.combo.get_model()
        iter = self.combo.get_active_iter()
        rowNo = model.get_path(iter)[0]
        self.assertEqual(rowNo, 2)
        self.assertEqual(model.get_value(iter, 0), 'Christian')
        self.assertEqual(model.get_value(iter, 1), 1976)
        self.assertRaises(KeyError, self.combo.select_item_by_data, 1980)

    def testGetSelectedData(self):
        self._prefill()
        self.combo.select_item_by_position(0)
        self.assertEqual(self.combo.get_selected_data(), 1981)
        self.assertRaises(TypeError,
                          self.combo.select_item_by_position, 'foobar')

    def testGetSelectedLabel(self):
        self._prefill()

    def testClear(self):
        self._prefill()
        self.combo.clear()
        self.assertEqual(map(list, self.combo.get_model()), [])


class FakeView:
    def handler_block(self, widget):
        pass

    def handler_unblock(self, widget):
        pass


class BaseModelTest:
    def setUp(self):
        self.model = Settable(attr=0)
        proxy = Proxy(FakeView(), self.model)
        self.combo = disabledeprecationcall(self.type)
        self.combo.data_type = int
        self.combo.model_attribute = 'attr'
        self.combo.prefill([('foo', 0),
                            ('bar', 1)])
        proxy.add_widget('attr', self.combo)
        self.combo.show()

    def testSelectItemByData(self):
        self.combo.select_item_by_data(1)
        self.assertEqual(self.model.attr, 1)
        self.combo.select_item_by_data(0)
        self.assertEqual(self.model.attr, 0)

    def testSelectItemBylabel(self):
        self.combo.select_item_by_label('bar')
        self.assertEqual(self.model.attr, 1)
        self.combo.select_item_by_label('foo')
        self.assertEqual(self.model.attr, 0)


class ComboModelTest(BaseModelTest, unittest.TestCase):
    type = ProxyComboBox

    def test_prefill_attr_none(self):
        model = Settable(attr=None)
        proxy = Proxy(FakeView(), model)
        combo = ProxyComboBox()
        combo.data_type = int
        combo.model_attribute = 'attr'
        combo.prefill([('foo', 10), ('bar', 20)])
        proxy.add_widget('attr', combo)

        # Even though attr is None, the combo doesn't allow something
        # not prefilled in it to be selected. In this case, it will select
        # the first item (prefill actually does that) instead.
        self.assertEqual(model.attr, 10)


class ComboEntryModelTest(BaseModelTest, unittest.TestCase):
    type = ProxyComboEntry

    def test_prefill_attr_none(self):
        model = Settable(attr=None)
        proxy = Proxy(FakeView(), model)
        combo = ProxyComboEntry()
        combo.data_type = int
        combo.model_attribute = 'attr'
        combo.prefill([('foo', 10), ('bar', 20)])
        proxy.add_widget('attr', combo)

        self.assertEqual(model.attr, None)


if __name__ == '__main__':
    unittest.main()
