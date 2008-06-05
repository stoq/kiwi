#!/usr/bin/env python
import unittest

from kiwi.ui.widgets.scale import ProxyHScale, ProxyVScale

class ScaleTest(unittest.TestCase):
    def testFloat(self):
        vscale = ProxyVScale()
        self.assertEqual(vscale.get_property("data-type"), 'float')

        hscale = ProxyHScale()
        self.assertEqual(hscale.get_property("data-type"), 'float')

if __name__ == '__main__':
    unittest.main()
