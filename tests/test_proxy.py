import unittest

from kiwi import ValueUnset
from kiwi.python import Settable
from kiwi.ui.proxy import Proxy
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.radiobutton import ProxyRadioButton
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox

class FakeView(object):
    def __init__(self):
        self.widgets = []

    def add(self, name, data_type, widget_type):
        widget = widget_type()
        widget.set_property('model-attribute', name)
        widget.set_property('data-type', data_type)

        setattr(self, name, widget)
        self.widgets.append(name)
        widget.show()
        return widget

    def handler_block(self, *args):
        pass

    def handler_unblock(self, *args):
        pass

class Model(Settable):
    def __init__(self):
        Settable.__init__(self,
                          entry='foo',
                          checkbutton=True,
                          radiobutton='first',
                          label='label',
                          spinbutton=100,
                          textview='sliff',
                          comboentry='CE1',
                          combobox='CB1')

class TestProxy(unittest.TestCase):
    def setUp(self):
        self.view = FakeView()
        self.view.add('checkbutton', bool, ProxyCheckButton)
        self.view.add('entry', str, ProxyEntry)
        self.view.add('label', str, ProxyLabel)
        self.view.add('spinbutton', int, ProxySpinButton)

        self.view.add('textview', str, ProxyTextView)
        self.radio_first = self.view.add('radiobutton', str, ProxyRadioButton)
        self.radio_first.set_property('data_value', 'first')
        self.radio_second = ProxyRadioButton()
        self.radio_second.set_group(self.radio_first)
        self.radio_second.set_property('data_value', 'second')

        self.comboentry = self.view.add('comboentry', str, ProxyComboEntry)
        self.comboentry.prefill(['CE1','CE2','CE3'])
        self.comboentry.show()

        self.combobox = self.view.add('combobox', str, ProxyComboBox)
        self.combobox.prefill(['CB1','CB2','CB3'])
        self.combobox.show()

        self.model = Model()
        self.proxy = Proxy(self.view, self.model, self.view.widgets)

    def testCheckButton(self):
        self.assertEqual(self.model.checkbutton, True)
        self.view.checkbutton.set_active(False)
        self.assertEqual(self.model.checkbutton, False)

    def testEntry(self):
        self.assertEqual(self.model.entry, 'foo')
        self.view.entry.set_text('bar')
        self.assertEqual(self.model.entry, 'bar')

    def testLabel(self):
        self.assertEqual(self.model.label, 'label')
        self.view.label.set_text('other label')
        self.assertEqual(self.model.label, 'other label')

    def testRadioButton(self):
        self.assertEqual(self.model.radiobutton, 'first')
        self.radio_second.set_active(True)
        self.assertEqual(self.model.radiobutton, 'second')
        self.radio_first.set_active(True)
        self.assertEqual(self.model.radiobutton, 'first')

    def testSpinButton(self):
        self.assertEqual(self.model.spinbutton, 100)
        self.view.spinbutton.set_text("200")
        self.assertEqual(self.model.spinbutton, 200)

    def testTextView(self):
        self.assertEqual(self.model.textview, 'sliff')
        self.view.textview.get_buffer().set_text('sloff')
        self.assertEqual(self.model.textview, 'sloff')

    def testComboEntry(self):
        self.assertEqual(self.model.comboentry, 'CE1')
        self.view.comboentry.select('CE2')
        self.assertEqual(self.model.comboentry, 'CE2')
        self.view.comboentry.entry.set_text('CENone')
        self.assertEqual(self.model.comboentry, None)

    def testComboBox(self):
        self.assertEqual(self.model.combobox, 'CB1')
        self.view.combobox.select('CB2')
        self.assertEqual(self.model.combobox, 'CB2')

    def testEmptyModel(self):
        self.radio_second.set_active(True)

        self.proxy.set_model(None)
        self.assertEqual(self.view.entry.read(), '')
        self.assertEqual(self.view.checkbutton.read(), False)
        self.assertEqual(self.view.radiobutton.read(), 'first')
        self.assertEqual(self.view.label.read(), '')
        self.assertEqual(self.view.spinbutton.read(), ValueUnset)
        self.assertEqual(self.view.textview.read(), '')
        self.assertEqual(self.view.comboentry.read(), None)
        self.assertEqual(self.view.combobox.read(), 'CB1')
