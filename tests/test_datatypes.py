from datetime import date
import unittest
import locale

from kiwi.datatypes import currency, converter, ValidationError

import utils

date_converter = converter.get_converter(date)
bool_converter = converter.get_converter(bool)

class DataTypesTest(unittest.TestCase):

    def teststr2bool(self):
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

    def teststr2date_esES(self):
        # set the date format to the spanish one
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')
            print 'skipping es_ES, locale not available'
        except locale.Error:
            return

        birthdate = date(1979, 2, 12)
        # in the spanish locale the format of a date is %d/%m/%y
        self.assertEqual(date_converter.from_string("12/2/79"), birthdate)
        self.assertEqual(date_converter.from_string("12/02/79"), birthdate)

    def teststr2date_ptBR(self):
        # let's try with the portuguese locale
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
            print 'skipping pt_BR, locale not available'
        except locale.Error:
            return

        birthdate = date(1979, 2, 12)
        # portuguese format is "%d-%m-%Y"
        self.assertEqual(date_converter.from_string("12-2-1979"), birthdate)
        self.assertEqual(date_converter.from_string("12-02-1979"), birthdate)

        # test some invalid dates
        self.assertRaises(ValidationError,
                          date_converter.from_string, "40-10-2005")
        # february only have 28 days
        self.assertRaises(ValidationError,
                          date_converter.from_string, "30-02-2005")

    def testdate2str_esES(self):
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')
        except locale.Error:
            print 'skipping es_ES, locale not available'
            return

        self.assertEqual(date_converter.as_string(date(1979, 2, 12)),
                         "12/02/79")

    def testdate2str_ptBR(self):
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
            print 'skipping pt_BR, locale not available'
        except locale.Error:
            return

        self.assertEqual(date_converter.as_string(date(1979, 2, 12)),
                         "12-02-1979")

    def testFormatPricePtBR(self):
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
        except locale.Error:
            print 'skipping pt_BR, locale not available'
            return

        self.assertEqual(currency(100).format(), 'R$100')
        self.assertEqual(currency(123.45).format(), 'R$123,45')
        self.assertEqual(currency(12345).format(), 'R$12.345')
        self.assertEqual(currency(-100).format(), 'R$-100')

    def testFormatPriceEnUS(self):
        try:
            locale.setlocale(locale.LC_TIME, 'en_US')
        except locale.Error:
            print 'skipping en_US, locale not available'
            return
        self.assertEqual(currency(100).format(), '$100')
        self.assertEqual(currency(123.45).format(), '$123.45')
        self.assertEqual(currency(12345).format(), '$12,345')
        self.assertEqual(currency(-100).format(), '$-100')
        self.assertEqual(currency(1).format(True), '$1')
        self.assertEqual(currency(1).format(False), '1')
        self.assertEqual(currency(0).format(True), '$0')

if __name__ == "__main__":
    unittest.main()
