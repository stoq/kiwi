#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
# 
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#

"""Data type converters with locale and currency support"""

import datetime
import locale
import sys
import time

from kiwi import ValueUnset

# by default locale uses the C locale but our date conversions use the user
# locale so we need to set the locale to that one
locale.setlocale(locale.LC_ALL, '') # this set the user locale ( $LANG )

__all__ = ['ValidationError', 'lformat', 'converter', 'format_price']

class ValidationError(Exception):
    pass

class ConverterRegistry:
    def __init__(self):
        self._converters = {}

    def add(self, converter_type):
        if not issubclass(converter_type, BaseConverter):
            raise TypeError("converter_type must be a BaseConverter subclass")

        c = converter_type()
        self._converters[c.type] = c

    def get_converter(self, converter_type):
        try:
            return self._converters[converter_type]
        except KeyError:
            raise KeyError(converter_type)
        
    def check_supported(self, data_type):
        value = None
        for t in self._converters.values():
            if t.type == data_type or t.type.__name__ == data_type:
                value = t.type
                break

        assert not isinstance(value, str), value
        
        if not value:
            type_names = [t.type.__name__ for t in self._converters.values()]
            raise TypeError("%s is not supported. Supported types are: %s"
                            % (data_type, ', '.join(type_names)))

        return value

    def as_string(self, converter_type, value, format=None):
        """
        Convert to a string
        @param converter_type:
        @param value:
        @param format:
        """
        c = self.get_converter(converter_type)
        if c.as_string is None:
            return value

        if not isinstance(value, c.type):
            raise TypeError('data: %s must be of %r not %r' % (
                value, c.type, type(value)))
        
        return c.as_string(value, format=format)
            
    def from_string(self, converter_type, value):
        """
        Convert from a string
        @param converter_type:
        @param value:
        """
        c = self.get_converter(converter_type)
        if c.from_string is None:
            return value

        return c.from_string(value)

    def str_to_type(self, value):
        for c in self._converters.values():
            if c.type.__name__ == value:
                return c.type

# Global converter, can be accessed from outside
converter = ConverterRegistry()

class BaseConverter(object):
    """
    Abstract converter used by all datatypes
    @cvar type:
    """
    type = None
    
    def get_compare_function(self):
        """
        @returns:
        """
        return cmp
    
    def as_string(self, value, format):
        """
        @param value:
        @param format:
        @returns:
        """
        
    def from_string(self, value):
        """
        @param value:
        @returns:
        """
        
class _StringConverter(BaseConverter):
    type = str
    
    def as_string(self, value, format=None):
        if format is None:
            format = '%s'
        return format % value

    def from_string(self, value):
        return str(value)
    
converter.add(_StringConverter)

class _IntConverter(BaseConverter):
    type = int

    def as_string(self, value, format=None):
        """Convert a float to a string"""
        if format is None:
            format = '%d'
        return lformat(format, value)

    def from_string(self, value):
        "Convert a string to an integer"
        if value == '':
            return ValueUnset
        
        conv = locale.localeconv()
        thousands_sep = conv["thousands_sep"]
        # Remove all thousand separators, so int() won't barf at us
        if thousands_sep and thousands_sep in value:
            value = value.replace(thousands_sep, '')

        try:
            return int(value)
        except ValueError:
            raise ValidationError(
                "%s could not be converted to an integer" % value)
        
converter.add(_IntConverter)
    
class _BoolConverter(BaseConverter):
    type = bool
    
    as_string = lambda s, value, format=None: str(value)

    def from_string(self, value):
        "Convert a string to a boolean"
        if value == '':
            return ValueUnset
        
        if value.upper() in ('TRUE', '1'):
            return True
        elif value.upper() in ('FALSE', '0'):
            return False

        return ValidationError("'%s' can not be converted to a boolean" % value)

converter.add(_BoolConverter)

class _FloatConverter(BaseConverter):
    type = float
    
    def _filter_locale(self, value):
        """
        Removes the locale specific data from the value string.
        Currently we only remove the thousands separator and
        convert the decimal point.
        The returned value of this function can safely be passed to float()
        """
        
        conv = locale.localeconv()

        # Check so we only have one decimal point
        decimal_point = conv["decimal_point"]
        decimal_points = value.count(decimal_point)
        if decimal_points == 1:
            # Replace the decimal point with a dot, which float() can handle
            value = value.replace(decimal_point, '.')
        elif decimal_points > 1:
            raise ValidationError(
                'You have more than one decimal point ("%s") '
                ' in your number "%s"' % (decimal_point, value))

        thousands_sep = conv["thousands_sep"]
        if not thousands_sep:
            return value
        
        # Check so we don't have any thousand separators to the right
        # of the decimal point
        th_sep_count = value.count(thousands_sep)
        if th_sep_count and decimal_points:
            decimal_point_pos = value.index(decimal_point)
            if thousands_sep in value[decimal_point_pos+1:]:
                raise ValidationError("You have a thousand separator to the "
                                      "right of the decimal point")
            check_value = value[:decimal_point_pos]
        else:
            check_value = value
            
        # Verify so the thousand separators are placed properly
        # TODO: Use conv['grouping'] for locales where it's not 3
        parts = check_value.split(thousands_sep)
        
        # First part is a special case, It can be 1, 2 or 3
        if 3 > len(parts[0]) < 1:
            raise ValidationError("Inproperly placed thousands separator") 

        # Middle parts should have a length of 3
        for part in parts[1:]:
            if len(part) != 3:
                raise ValidationError("Inproperly placed thousand "
                                      "separators") 

        # Remove all thousand separators
        return value.replace(thousands_sep, '')

    def as_string(self, value, format=None):
        """Convert a float to a string"""
        if format is None:
            format = '%f'
        return lformat(format, value)

    def from_string(self, value):
        """Convert a string to a float"""

        if value == '':
            return ValueUnset
        
        value = self._filter_locale(value)

        try:
            retval = float(value)
        except ValueError:
            raise ValidationError("This field requires a number")

        return retval
    
converter.add(_FloatConverter)

class _BaseDateTimeConverter(BaseConverter):
    """
    Abstract class for converting datatime objects to and from strings
    @cvar date_format:
    @cvar lang_constant:
    """
    date_format = None

    def get_lang_constant(self):
        # This is a method and not a class variable since it does not
        # exist on all supported platforms, eg win32
        raise NotImplementedError
    
    def from_datainfo(self, dateinfo):
        raise NotImplementedError
    
    def get_compare_function(self):
        # Provide a special comparison function that allows None to be
        # used, which the __cmp__/__eq__ methods for datatime objects doesn't
        def _datecmp(a, b):
            if a is None:
                if b is None:
                    return 0
                return 1
            elif b is None:
                return -1
            else:
                return cmp(a, b)
        return _datecmp

    def _get_format(self):
        if sys.platform == 'win32':
            return self.date_format
        
        return locale.nl_langinfo(self.lang_constant)
    
    def as_string(self, value, format=None):
        "Convert a date to a string"
        if format is None:
            format = self._get_format()
            
        if value is None:
            return ''
        
        return value.strftime(format)
    
    def from_string(self, value):
        "Convert a string to a date"

        if value == "":
            return None
        
        # We're only supporting strptime values for now,
        # perhaps we should add macros, to be able to write
        # yyyy instead of %Y
        
        format = self._get_format()
        try:
            dateinfo = time.strptime(value, format)
            return self.from_dateinfo(dateinfo)
        except ValueError:
            raise ValidationError(
                'This field requires a date of the format "%s" and '
                'not "%s"' % (format, value))

class _TimeConverter(_BaseDateTimeConverter):
    type = datetime.time
    date_format = '%X'
    def get_lang_constant(self):
        return locale.T_FMT
converter.add(_TimeConverter)

class _DateTimeConverter(_BaseDateTimeConverter):
    type = datetime.datetime
    date_format = '%c'
    def get_lang_constant(self):
        return locale.D_T_FMT
converter.add(_DateTimeConverter)

class _DateConverter(_BaseDateTimeConverter):
    type = datetime.date
    date_format = '%x'
    def get_lang_constant(self):
        return locale.D_FMT

    def from_dateinfo(self, dateinfo):
        return datetime.date(*dateinfo[:3]) # year, month, day
converter.add(_DateConverter)

class _ObjectConverter(BaseConverter):
    type = object
    
    as_string = None
    from_string = None
converter.add(_ObjectConverter)

class currency(float):
    """
    A datatype representing currency, used together with the list and
    the framework
    """
    _converter = converter.get_converter(float)
    
    def __new__(cls, value):
        """
        @param value: value to convert
        @type value: string or number
        """
        if isinstance(value, str):
            conv = locale.localeconv()
            currency_symbol = conv.get('currency_symbol')
            text = value.strip(currency_symbol)
            value = currency._converter.from_string(text)
        elif not isinstance(value, (int, float, long)):
            raise TypeError(
                "cannot convert %r of type %s to a currency" % (
                value, type(value)))
        return float.__new__(cls, value)

    def format(self, symbol=True, precision=None):
        value = float(self)
        
        conv = locale.localeconv()

        # Grouping (eg thousand separator) of integer part
        groups = conv.get('mon_grouping', [])[:]
        groups.reverse()
        if groups:
            group = groups.pop()
        else:
            group = 3

        intparts = []

        # We're iterating over every character in the integer part
        # make sure to remove the negative sign, it'll be added later
        intpart = str(int(abs(value)))

        while True:
            if not intpart:
                break

            s = intpart[-group:]
            intparts.insert(0, s)
            intpart = intpart[:-group]
            if not groups:
                continue

            last = groups.pop()
            # if 0 reuse last one, see struct lconv in locale.h
            if last != 0:
                group = last

        # Add the sign, and the list of decmial parts, which now are grouped
        # properly and can be joined by mon_thousand_sep
        if value > 0:
            sign = conv.get('positive_sign', '')
        elif value < 0:
            sign = conv.get('negative_sign', '-')
        else:
            sign = ''
        currency = sign + conv.get('mon_thousands_sep', '.').join(intparts)

        # Only add decimal part if it has one, is this correct?
        if precision is not None or value % 1 != 0:
            # Pythons string formatting can't handle %.127f
            # 127 is the default value from glibc/python
            if precision:
                frac_digits = precision
            else:
                frac_digits = conv.get('frac_digits', 2)
                if frac_digits == 127:
                    frac_digits = 2

            format = '%%.%sf' % frac_digits
            dec_part = (format % value)[-frac_digits:]

            mon_decimal_point = conv.get('mon_decimal_point', '.')
            currency += mon_decimal_point + dec_part

        # If requested include currency symbol 
        currency_symbol = conv.get('currency_symbol', '')
        if currency_symbol and symbol:
            if value > 0:
                cs_precedes = conv.get('p_cs_precedes', 1)
                sep_by_space = conv.get('p_sep_by_space', 1)
            else:
                cs_precedes = conv.get('n_cs_precedes', 1)
                sep_by_space = conv.get('n_sep_by_space', 1)

            # Patching glibc's output
            # See http://sources.redhat.com/bugzilla/show_bug.cgi?id=1294
            current_locale = locale.getlocale(locale.LC_MONETARY)
            if current_locale[0] == 'pt_BR':
                cs_precedes = 1
                sep_by_space = 0

            if sep_by_space:
                space = ' '
            else:
                space = ''
            if cs_precedes:
                currency = currency_symbol + space + currency
            else:
                currency = currency + space + currency_symbol

        return currency

    def __repr__(self):
        return '<currency %s> ' % self.format()
    
class _CurrencyConverter(BaseConverter):
    type = currency

    def __init__(self):
        self.symbol = True
        self.precision = 2
    
    def as_string(self, value, format=None):
        if format:
            raise TypeError("format is not supported for currency")
        
        if not isinstance(value, currency):
            try:
                value = currency(value)
            except ValueError:
                raise ValidationError(
                    "%s can not be converted to a currency" % value)

        return value.format(self.symbol, self.precision)

    def from_string(self, value):
        if value == '':
            return ValueUnset
        try:
            return currency(value)
        except ValueError:
            raise ValidationError(
                "%s can not be converted to a currency" % value)
        
converter.add(_CurrencyConverter)

def lformat(format, value):
    """Like locale.format but with grouping enabled"""
    return locale.format(format, value, 1)

def format_price(value, symbol=True, precision=None):
    """
    Formats a price according to the current locales monetary
    settings
    
    @param value: number
    @param symbol: whether to include the currency symbol
    """
    
    return currency(value).format(symbol, precision)

if __name__ == '__main__':
    print currency(10.0)
    print currency(10.3)
