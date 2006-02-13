from datetime import date
import unittest
import locale

from kiwi.datatypes import currency, converter, ValidationError

import utils

date_converter = converter.get_converter(date)
bool_converter = converter.get_converter(bool)

def set_locale(category, name):
    # set the date format to the spanish one
    try:
        locale.setlocale(category, name)
    except locale.Error:
        print 'skipping %s, locale not available' % name
        return False
    return True

class DataTypesTest(unittest.TestCase):
    def testFromString(self):
        self.assertEqual(bool_converter.from_string('TRUE'), True)
        self.assertEqual(bool_converter.from_string('true'), True)
        self.assertEqual(bool_converter.from_string('TrUe'), True)
        self.assertEqual(bool_converter.from_string('1'), True)
        self.assertEqual(bool_converter.from_string('FALSE'), False)
        self.assertEqual(bool_converter.from_string('false'), False)
        self.assertEqual(bool_converter.from_string('FalSE'), False)
        self.assertEqual(bool_converter.from_string('0'), False)

        # you are not supposed to pass something that is not a string
        self.assertRaises(AttributeError, bool_converter.from_string, None)

class DateTest(unittest.TestCase):
    def setUp(self):
        self.date = date(1979, 2, 12)

    def testFromStringES(self):
        if not set_locale(locale.LC_TIME, 'es_ES'):
            return

        self.assertEqual(date_converter.from_string("12/2/79"), self.date)
        self.assertEqual(date_converter.from_string("12/02/79"), self.date)

    def testAsStringES(self):
        if not set_locale(locale.LC_TIME, 'es_ES'):
            return

        self.assertEqual(date_converter.as_string(self.date), "12/02/79")

    def tesFromStringBR(self):
        if not set_locale(locale.LC_TIME, 'pt_BR'):
            return

        self.assertEqual(date_converter.from_string("12-2-1979"), self.date)
        self.assertEqual(date_converter.from_string("12-02-1979"), self.date)

        # test some invalid dates
        self.assertRaises(ValidationError,
                          date_converter.from_string, "40-10-2005")
        self.assertRaises(ValidationError,
                          date_converter.from_string, "30-02-2005")

    def testAsStringBR(self):
        if not set_locale(locale.LC_TIME, 'pt_BR'):
            return

        self.assertEqual(date_converter.as_string(self.date), "12-02-1979")

class CurrencyTest(unittest.TestCase):
    def testFormatBR(self):
        if not set_locale(locale.LC_MONETARY, 'pt_BR'):
            return

        self.assertEqual(currency(100).format(), 'R$100')
        self.assertEqual(currency(123.45).format(), 'R$123,45')
        self.assertEqual(currency(12345).format(), 'R$12.345')
        self.assertEqual(currency(-100).format(), 'R$-100')

    def testFormatUS(self):
        if not set_locale(locale.LC_MONETARY, 'en_US'):
            return

        self.assertEqual(currency(100).format(), '$100')
        self.assertEqual(currency(123.45).format(), '$123.45')
        self.assertEqual(currency(12345).format(), '$12,345')
        self.assertEqual(currency(-100).format(), '$-100')
        self.assertEqual(currency(1).format(True), '$1')
        self.assertEqual(currency(1).format(False), '1')
        self.assertEqual(currency(0).format(True), '$0')

class UnicodeTest(unittest.TestCase):
    def setUp(self):
        self.conv = converter.get_converter(unicode)

    def testFromString(self):
        self.assertEqual(self.conv.from_string('foobar'), u'foobar')
        # utf-8 encoded, as default after importing gtk
        self.assertEqual(self.conv.from_string('\xc3\xa4'), u'\xe4')

    def testAsString(self):
        self.assertEqual(self.conv.as_string(u'foobar'), 'foobar')
        self.assertEqual(self.conv.as_string(u'\xe4'), '\xc3\xa4')

if __name__ == "__main__":
    unittest.main()
