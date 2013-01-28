#!/usr/bin/env python
import unittest

import gtk

from kiwi.ui.dialogs import selectfile


class TestSelectfile(unittest.TestCase):
    def testSelectfile(self):
        filters = gtk.FileFilter()
        filters.add_pattern('*.pdf')
        filters = [filters]

        with selectfile(filters=filters) as sf:
            self.assertTrue(isinstance(sf, gtk.FileChooserDialog))
            self.assertEqual(sf.list_filters(), filters)


if __name__ == '__main__':
    unittest.main()
