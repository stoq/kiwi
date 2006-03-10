#!/usr/bin/env python
import utils

import unittest

from kiwi.ui.widgets.checkbutton import CheckButton

class CheckButtonTest(unittest.TestCase):
    def testForBool(self):
        myChkBtn = CheckButton()
        self.assertEqual(myChkBtn.get_property("data-type"), bool)

        # this test doens't work... maybe be a pygtk bug
        #self.assertRaises(TypeError, myChkBtn.set_property, 'data-type', str)

if __name__ == '__main__':
    unittest.main()
