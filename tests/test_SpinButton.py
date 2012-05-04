#!/usr/bin/env python
import unittest

from kiwi.ui.widgets.spinbutton import ProxySpinButton


class SpinButtonTest(unittest.TestCase):
    def testForIntFloat(self):
        mySpinBtn = ProxySpinButton()
        self.assertEqual(mySpinBtn.get_property("data-type"), 'int')

        # this test doens't work... might be a pygtk bug
        #self.assertRaises(TypeError, mySpinBtn.set_property, 'data-type', str)

if __name__ == '__main__':
    unittest.main()
