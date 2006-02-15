import unittest

import gobject

from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.utils import PropertyObject, gproperty, HAVE_2_6

class Test(gobject.GObject, PropertyObject):
    __gtype_name__ = 'Test'
    gproperty('str-prop', str, nick='Nick', blurb='Blurb',
              default='Default')

    def __init__(self, **kwargs):
        gobject.GObject.__init__(self)
        PropertyObject.__init__(self, **kwargs)

class GPropertyTest(unittest.TestCase):
    def testProperties(self):
        for pspec in gobject.list_properties(Test):
            self.assertEqual(pspec.name, 'str-prop')
            self.assertEqual(pspec.nick, 'Nick', pspec.nick)
            self.assertEqual(pspec.default_value, 'Default',
                             pspec.default_value)
            self.assertEqual(pspec.blurb, 'Blurb', pspec.blurb)

class Subclassing(unittest.TestCase):
    def testSimple(self):
        subtype = type('Test2', (Test,), {})
        self.failUnless(issubclass(subtype, Test))
        instance = subtype()
        self.failUnless(isinstance(instance, Test))
        self.failUnless(isinstance(instance, subtype))

    def testCombo(self):
        self.assertEqual(getattr(ProxyComboBox, '__gsignals__', {}), {})
        self.assertEqual(getattr(ProxyComboBox, '__gproperties__', {}), {})
        subentry = type('MyClass', (ProxyComboBox,), {})
        self.assertNotEqual(gobject.type_name(subentry),
                            gobject.type_name(ProxyComboBox))

class MixinTest(unittest.TestCase):
    def testProperties(self):
        class Mixin(object):
            gproperty('mixin-prop', str, default='foo')

        class Object(gobject.GObject, PropertyObject, Mixin):
            gproperty('normal-prop', str, default='bar')

            def __init__(self, **kwargs):
                gobject.GObject.__init__(self)
                PropertyObject.__init__(self, **kwargs)

        o = Object()

        self.failUnless(hasattr(o, 'normal_prop'))
        self.assertEqual(o.normal_prop, 'bar')
        self.failUnless(hasattr(o, 'mixin_prop'))
        self.assertEqual(o.mixin_prop, 'foo')

    def testSpinButton(self):
        from kiwi.ui.widgets.spinbutton import SpinButton
        s = SpinButton()
        self.failUnless(hasattr(s, 'data_type'))
        self.assertEqual(s.data_type, int)

    def testTypeName(self):
        class Object(gobject.GObject, PropertyObject):
            __gtype_name__ = 'Object'
        if HAVE_2_6:
            return
        self.assertEqual(gobject.type_name(Object), 'Object')

if __name__ == '__main__':
    unittest.main()
