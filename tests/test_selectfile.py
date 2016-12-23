#!/usr/bin/env python
import unittest

from gi.repository import Gtk

from kiwi.ui.dialogs import selectfile


class TestSelectfile(unittest.TestCase):
    def testSelectfile(self):
        filters = Gtk.FileFilter()
        filters.add_pattern('*.pdf')
        filters = [filters]

        with selectfile(filters=filters) as sf:
            self.assertTrue(isinstance(sf, Gtk.FileChooserDialog))
            self.assertEqual(sf.list_filters(), filters)


if __name__ == '__main__':
    unittest.main()
