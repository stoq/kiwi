import sys
import datetime
import unittest

from kiwi.ui.dateentry import DateEntry

class TestDateEntry(unittest.TestCase):
    def setUp(self):
        self.date = datetime.date.today()

    def testGetSetDate(self):
        if sys.platform == 'win32':
            return
        entry = DateEntry()
        entry.set_date(self.date)
        self.assertEqual(entry.get_date(), self.date)

if __name__ == '__main__':
    unittest.main()
