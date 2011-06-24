import sys
import unittest

from gtk import gdk

from kiwi import ValueUnset
from kiwi.datatypes import converter
from kiwi.environ import environ
from kiwi.python import Settable
from kiwi.ui.proxy import Proxy
from kiwi.ui.widgets.button import ProxyButton
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.radiobutton import ProxyRadioButton
from kiwi.ui.widgets.scale import ProxyHScale, ProxyVScale
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
                          hscale=100.0,
                          vscale=100.0,
                          textview='sliff',
                          comboentry='CE1',
                          combobox='CB1',
                          button='button')

class TestProxy(unittest.TestCase):
    def setUp(self):
        self.view = FakeView()
        self.view.add('checkbutton', bool, ProxyCheckButton)
        self.view.add('entry', str, ProxyEntry)
        self.view.add('label', str, ProxyLabel)
        self.view.add('spinbutton', int, ProxySpinButton)
        self.view.add('hscale', float, ProxyHScale)
        self.view.add('vscale', float, ProxyVScale)
        self.view.add('button', str, ProxyButton)
        self.view.add('buttonpixbuf', gdk.Pixbuf, ProxyButton)

        self.view.add('textview', str, ProxyTextView)
        self.radio_first = self.view.add('radiobutton', str, ProxyRadioButton)
        self.radio_first.set_property('data_value', 'first')
        self.radio_second = ProxyRadioButton()
        self.radio_second.set_group(self.radio_first)
        self.radio_second.set_property('data_value', 'second')

        self.view.hscale.get_adjustment().upper = 200
        self.view.vscale.get_adjustment().upper = 250

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

    def testHScale(self):
        self.assertEqual(self.model.vscale, 100)
        self.view.vscale.set_value(220)
        self.assertEqual(self.model.vscale, 220)

    def testVScale(self):
        self.assertEqual(self.model.vscale, 100)
        self.view.vscale.set_value(200)
        self.assertEqual(self.model.vscale, 200)

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

    def testButton(self):
        self.assertEqual(self.model.button, 'button')
        self.view.button.update('sliff')
        self.assertEqual(self.model.button, 'sliff')

    def testButtonPixbuf(self):
        if sys.platform == 'win32':
            return

        filename = environ.find_resource('pixmap', 'validation-error-16.png')
        pixbuf = gdk.pixbuf_new_from_file(filename)
        #self.assertEqual(self.view.buttonpixbuf.data_type, 'Pixbuf')
        self.view.buttonpixbuf.update(pixbuf)
        self.assertEqual(type(self.view.buttonpixbuf.read()), gdk.Pixbuf)
        conv = converter.get_converter(gdk.Pixbuf)
        self.assertEqual(conv.as_string(self.model.buttonpixbuf),
                         conv.as_string(pixbuf))
        self.view.buttonpixbuf.update(None)
        self.assertEqual(self.view.buttonpixbuf.read(), None)
        self.assertEqual(self.model.buttonpixbuf, None)

    def testEmptyModel(self):
        self.radio_second.set_active(True)

        self.proxy.set_model(None)

        self.assertEqual(self.view.entry.read(), ValueUnset)
        self.assertEqual(self.view.checkbutton.read(), False)
        self.assertEqual(self.view.radiobutton.read(), 'first')
        self.assertEqual(self.view.label.read(), '', 'label')
        self.assertEqual(self.view.spinbutton.read(), ValueUnset, 'spinbutton')
        self.assertEqual(self.view.textview.read(), ValueUnset, 'textview')
        self.assertEqual(self.view.comboentry.read(), None, 'comboentry')
        self.assertEqual(self.view.combobox.read(), 'CB1', 'combobox')

    def testValueUnset(self):
        self.view.entry.update(ValueUnset)
        self.assertEqual(self.view.entry.get_text(), "")
        self.view.spinbutton.update(ValueUnset)
        self.assertEqual(self.view.spinbutton.get_text(), "")
