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

    def teststr2date(self):
        # set the date format to the spanish one
        locale.setlocale(locale.LC_TIME, 'es_ES')

        birthdate = date(1979, 2, 12)
        # in the spanish locale the format of a date is %d/%m/%y
        self.assertEqual(date_converter.from_string("12/2/79"), birthdate)
        self.assertEqual(date_converter.from_string("12/02/79"), birthdate)

        # let's try with the portuguese locale
        locale.setlocale(locale.LC_TIME, 'pt_BR')

        # portuguese format is "%d-%m-%Y"
        self.assertEqual(date_converter.from_string("12-2-1979"), birthdate)
        self.assertEqual(date_converter.from_string("12-02-1979"), birthdate)

        # test some invalid dates
        self.assertRaises(ValidationError,
                          date_converter.from_string, "40-10-2005")
        # february only have 28 days
        self.assertRaises(ValidationError,
                          date_converter.from_string, "30-02-2005")
        
    def testdate2str(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')

        birthdate = date(1979, 2, 12)

        self.assertEqual(date_converter.as_string(birthdate), "12/02/79")

        locale.setlocale(locale.LC_TIME, 'pt_BR')

        self.assertEqual(date_converter.as_string(birthdate), "12-02-1979")

    def testFormatPricePtBR(self):
        self.assertEqual(locale.setlocale(locale.LC_MONETARY, 'pt_BR'),
                         'pt_BR',
                         'pt_BR locale is required to run this test')
        self.assertEqual(currency(100).format(), 'R$100')
        self.assertEqual(currency(123.45).format(), 'R$123,45')
        self.assertEqual(currency(12345).format(), 'R$12.345')
        self.assertEqual(currency(-100).format(), 'R$-100')

    def testFormatPriceEnUS(self):
        self.assertEqual(locale.setlocale(locale.LC_MONETARY, 'en_US'),
                         'en_US',
                         'en_US locale is required to run this test')
        self.assertEqual(currency(100).format(), '$100')
        self.assertEqual(currency(123.45).format(), '$123.45')
        self.assertEqual(currency(12345).format(), '$12,345')
        self.assertEqual(currency(-100).format(), '$-100')
        self.assertEqual(currency(1).format(True), '$1')
        self.assertEqual(currency(1).format(False), '1')

if __name__ == "__main__":
    unittest.main()
