from decimal import Decimal
import datetime
import unittest
import locale

from kiwi.datatypes import currency, converter, ValidationError, ValueUnset

import utils

def set_locale(category, name):
    # set the date format to the spanish one
    try:
        locale.setlocale(category, name)
    except locale.Error:
        print 'skipping %s, locale not available' % name
        return False
    return True

class DataTypesTest(unittest.TestCase):
    def setUp(self):
        self.date = datetime.date(1979, 2, 12)
        self.conv = converter.get_converter(bool)

    def testFromString(self):
        self.assertEqual(self.conv.from_string('TRUE'), True)
        self.assertEqual(self.conv.from_string('true'), True)
        self.assertEqual(self.conv.from_string('TrUe'), True)
        self.assertEqual(self.conv.from_string('1'), True)
        self.assertEqual(self.conv.from_string('FALSE'), False)
        self.assertEqual(self.conv.from_string('false'), False)
        self.assertEqual(self.conv.from_string('FalSE'), False)
        self.assertEqual(self.conv.from_string('0'), False)

        # you are not supposed to pass something that is not a string
        self.assertRaises(AttributeError, self.conv.from_string, None)

class DateTest(unittest.TestCase):
    def setUp(self):
        self.date = datetime.date(1979, 2, 12)
        self.conv = converter.get_converter(datetime.date)

    def tearDown(self):
        set_locale(locale.LC_ALL, 'C')

    def testFromStringES(self):
        if not set_locale(locale.LC_TIME, 'es_ES'):
            return

        self.assertEqual(self.conv.from_string("12/2/79"), self.date)
        self.assertEqual(self.conv.from_string("12/02/79"), self.date)

    def testAsStringES(self):
        if not set_locale(locale.LC_TIME, 'es_ES'):
            return

        self.assertEqual(self.conv.as_string(self.date), "12/02/79")

    def tesFromStringBR(self):
        if not set_locale(locale.LC_TIME, 'pt_BR'):
            return

        self.assertEqual(self.conv.from_string("12-2-1979"), self.date)
        self.assertEqual(self.conv.from_string("12-02-1979"), self.date)

        # test some invalid dates
        self.assertRaises(ValidationError,
                          self.conv.from_string, "40-10-2005")
        self.assertRaises(ValidationError,
                          self.conv.from_string, "30-02-2005")

    def testAsStringBR(self):
        if not set_locale(locale.LC_TIME, 'pt_BR'):
            return

        self.assertEqual(self.conv.as_string(self.date), "12-02-1979")

class CurrencyTest(unittest.TestCase):
    def setUp(self):
        self.conv = converter.get_converter(currency)

    def tearDown(self):
        set_locale(locale.LC_ALL, 'C')

    def testFormatBR(self):
        if not set_locale(locale.LC_MONETARY, 'pt_BR'):
            return

        self.assertEqual(currency(100).format(), 'R$100')
        self.assertEqual(currency('123.45').format(), 'R$123,45')
        self.assertEqual(currency(12345).format(), 'R$12.345')
        self.assertEqual(currency(-100).format(), 'R$-100')

        self.assertEqual(self.conv.from_string('0,5'), currency('0.5'))

    def testFormatUS(self):
        if not set_locale(locale.LC_MONETARY, 'en_US'):
            return

        self.assertEqual(currency(100).format(), '$100')
        self.assertEqual(currency('123.45').format(), '$123.45')
        self.assertEqual(currency(12345).format(), '$12,345')
        self.assertEqual(currency(-100).format(), '$-100')
        self.assertEqual(currency(1).format(True), '$1')
        self.assertEqual(currency(1).format(False), '1')
        self.assertEqual(currency(0).format(True), '$0')

        self.assertEqual(self.conv.from_string(''), ValueUnset)
        self.assertEqual(self.conv.from_string('0'), currency(0))
        self.assertEqual(self.conv.from_string('0.5'), currency('0.5'))
        self.assertRaises(ValidationError, self.conv.from_string, 'foo')

        self.assertEqual(self.conv.as_string(currency(0)), '$0.00')
        self.assertEqual(self.conv.as_string(currency(-10)), '$-10.00')
        #self.assertEqual(ValidationError, self.conv.as_string, object)

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

class IntTest(unittest.TestCase):
    def setUp(self):
        self.conv = converter.get_converter(int)

    def testFromString(self):
        self.assertEqual(self.conv.from_string('0'), 0)
        self.assertRaises(ValidationError, self.conv.from_string, '0.5')

    def testAsString(self):
        self.assertEqual(self.conv.as_string(0), '0')
        self.assertEqual(self.conv.as_string(-10), '-10')

class FloatTest(unittest.TestCase):
    def setUp(self):
        self.conv = converter.get_converter(float)

    def tearDown(self):
        set_locale(locale.LC_ALL, 'C')

    def testFromString(self):
        self.assertEqual(self.conv.from_string('-2.5'), -2.5)
        self.assertEqual(self.conv.from_string('10.33'), 10.33)
        self.assertRaises(ValidationError, self.conv.from_string, 'foo')
        self.assertRaises(ValidationError, self.conv.from_string, '1.2.3')
        self.assertEqual(self.conv.from_string(''), ValueUnset)

    def testFromStringUS(self):
        if not set_locale(locale.LC_NUMERIC, 'en_US'):
            return
        self.assertEqual(self.conv.from_string('0.'), 0)
        self.assertEqual(self.conv.from_string('1.75'), 1.75)
        self.assertEqual(self.conv.from_string('10,000'), 10000)
        self.assertEqual(self.conv.from_string('10,000,000.5'), 10000000.5)

    def testFromStringSE(self):
        # Swedish is interesting here because it has different
        # thousand separator and decimal points (compared to en_US)
        if not set_locale(locale.LC_NUMERIC, 'sv_SE'):
            return
        self.assertEqual(self.conv.from_string('0,'), 0)
        self.assertEqual(self.conv.from_string('1,75'), 1.75)
        self.assertEqual(self.conv.from_string('4 321'), 4321)
        self.assertEqual(self.conv.from_string('54 321'), 54321)
        self.assertEqual(self.conv.from_string('654 321'), 654321)
        self.assertEqual(self.conv.from_string('7 654 321'), 7654321)
        self.assertEqual(self.conv.from_string('10 000 000,5'), 10000000.5)
        self.assertRaises(ValidationError, self.conv.from_string, '1,2 3')
        self.assertRaises(ValidationError, self.conv.from_string, '1 23 ')
        self.assertRaises(ValidationError, self.conv.from_string, ' 23 ')
        #self.assertRaises(ValidationError, self.conv.from_string, '1234 234')

    def testAsString(self):
        self.assertEqual(self.conv.as_string(0.5), '0.5')
        self.assertEqual(self.conv.as_string(-10.5), '-10.5')
        self.assertEqual(self.conv.as_string(0.5), '0.5')

class DecimalTest(unittest.TestCase):
    def setUp(self):
        self.conv = converter.get_converter(Decimal)

    def testFromString(self):
        self.assertEqual(self.conv.from_string('-2.5'), Decimal('-2.5'))
        self.assertEqual(self.conv.from_string('10.33'), Decimal('10.33'))
        self.assertRaises(ValidationError, self.conv.from_string, 'foo')
        self.assertRaises(ValidationError, self.conv.from_string, '1.2.3')
        self.assertEqual(self.conv.from_string(''), ValueUnset)

if __name__ == "__main__":
    unittest.main()
