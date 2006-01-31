import unittest

import gobject

from kiwi.utils import PropertyObject, gproperty

class Test(PropertyObject, gobject.GObject):
    gproperty('str-prop', str, nick='Nick', blurb='Blurb',
              default='Default')

    def __init__(self, **kwargs):
        PropertyObject.__init__(self, **kwargs)
        gobject.GObject.__init__(self)

class GPropertyTest(unittest.TestCase):
    def testProperties(self):
        for pspec in gobject.list_properties(Test):
            self.assertEqual(pspec.name, 'str-prop')
            self.assertEqual(pspec.nick, 'Nick', pspec.nick)
            self.assertEqual(pspec.default_value, 'Default',
                             pspec.default_value)
            self.assertEqual(pspec.blurb, 'Blurb', pspec.blurb)

if __name__ == '__main__':
    unittest.main()
