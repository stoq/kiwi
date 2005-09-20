from datetime import date
import unittest
import locale

from kiwi import datatypes

import utils

class DataTypesTest(unittest.TestCase):

    def teststr2bool(self):
        bool_converter = datatypes.BoolConverter()

        self.assertEqual(bool_converter.from_string('TRUE'), True)
        self.assertEqual(bool_converter.from_string('true'), True)
        self.assertEqual(bool_converter.from_string('TrUe'), True)
        self.assertEqual(bool_converter.from_string('1'), True)
        self.assertEqual(bool_converter.from_string('FALSE'), False)
        self.assertEqual(bool_converter.from_string('false'), False)
        self.assertEqual(bool_converter.from_string('FalSE'), False)
        self.assertEqual(bool_converter.from_string('0'), False)

        # testing with default values
        self.assertEqual(bool_converter.from_string('something', False), False)
        self.assertEqual(bool_converter.from_string('something', True), True)
        self.assertEqual(bool_converter.from_string('', True), True)
        self.assertEqual(bool_converter.from_string('', False), False)

        # you are not supposed to pass something that is not a string
        self.assertRaises(AttributeError, bool_converter.from_string, None)

    def teststr2date(self):
        # set the date format to the spanish one
        locale.setlocale(locale.LC_TIME, 'es_ES')
        date_converter = datatypes.DateConverter()

        birthdate = date(1979, 2, 12)
        # in the spanish locale the format of a date is %d/%m/%y
        self.assertEqual(date_converter.from_string("12/2/79"), birthdate)
        self.assertEqual(date_converter.from_string("12/02/79"), birthdate)

        # let's try with the portuguese locale
        locale.setlocale(locale.LC_TIME, 'pt_BR')
        date_converter.update_format()

        # portuguese format is "%d-%m-%Y"
        self.assertEqual(date_converter.from_string("12-2-1979"), birthdate)
        self.assertEqual(date_converter.from_string("12-02-1979"), birthdate)

        # test some invalid dates
        self.assertRaises(datatypes.ValidationError,
                          date_converter.from_string, "40-10-2005")
        # february only have 28 days
        self.assertRaises(datatypes.ValidationError,
                          date_converter.from_string, "30-02-2005")
        
    def testdate2str(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')
        date_converter = datatypes.DateConverter()

        birthdate = date(1979, 2, 12)

        self.assertEqual(date_converter.as_string(birthdate), "12/02/79")

        locale.setlocale(locale.LC_TIME, 'pt_BR')
        date_converter.update_format()

        self.assertEqual(date_converter.as_string(birthdate), "12-02-1979")

    def testFormatPricePtBR(self):
        self.assertEqual(locale.setlocale(locale.LC_MONETARY, 'pt_BR'),
                         'pt_BR',
                         'pt_BR locale is required to run this test')
        self.assertEqual(datatypes.format_price(100), 'R$100')
        self.assertEqual(datatypes.format_price(123.45), 'R$123,45')
        self.assertEqual(datatypes.format_price(12345), 'R$12.345')
        self.assertEqual(datatypes.format_price(-100), 'R$-100')

    def testFormatPriceEnUS(self):
        self.assertEqual(locale.setlocale(locale.LC_MONETARY, 'en_US'),
                         'en_US',
                         'en_US locale is required to run this test')
        self.assertEqual(datatypes.format_price(100), '$100')
        self.assertEqual(datatypes.format_price(123.45), '$123.45')
        self.assertEqual(datatypes.format_price(12345), '$12,345')
        self.assertEqual(datatypes.format_price(-100), '$-100')
        self.assertEqual(datatypes.format_price(1, True), '$1')
        self.assertEqual(datatypes.format_price(1, False), '1')

if __name__ == "__main__":
    unittest.main()
