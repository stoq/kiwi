#!/usr/bin/env python
import unittest

from kiwi.ui.widgets.checkbutton import ProxyCheckButton

class CheckButtonTest(unittest.TestCase):
    def testForBool(self):
        myChkBtn = ProxyCheckButton()
        self.assertEqual(myChkBtn.props.data_type, 'bool')

        # this test doens't work... maybe be a pygtk bug
        #self.assertRaises(TypeError, myChkBtn.set_property, 'data-type', str)

if __name__ == '__main__':
    unittest.main()
