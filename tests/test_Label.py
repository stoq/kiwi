#!/usr/bin/env python
import unittest

from kiwi.ui.widgets.label import ProxyLabel


class LabelTest(unittest.TestCase):
    def testAttr(self):
        label = ProxyLabel()
        label.set_text("test label")
        label.set_italic(True)
        self.assertEqual(label.get_label(),
                         '<span style="italic">test label</span>')

        label.set_bold(True)
        label.set_size("xx-small")
        self.assertEqual(label.get_label(),
                         '<span size="xx-small" style="italic" weight="bold">'
                         'test label</span>')

        label.set_italic(True)
        label.set_bold(False)
        label.set_size("xx-large")
        self.assertEqual(label.get_label(),
                         '<span size="xx-large" style="italic">'
                         'test label</span>')

        label.set_bold(True)
        label.set_label("<b>different label</b>")
        label.set_text("test one more label")
        label.set_size("xx-small")
        self.assertEqual(label.get_label(),
                         '<span size="xx-small" style="italic" weight="bold">'
                         'test one more label</span>')

        self.assertRaises(ValueError, label.set_size, "wrong size")

if __name__ == '__main__':
    unittest.main()
