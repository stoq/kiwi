#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
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
#            Johan Dahlin <jdahlin@async.com.br>
#            Ronaldo Maia <romaia@async.com.br>
#

"""Data type converters with locale and currency support.

Provides routines for converting data to and from strings.
Simple example:

    >>> from kiwi.datatypes import converter
    >>> converter.from_string(int, '1,234')
    '1234'
    >>> converter.from_string(float, '1,234')
    '1234.0'
    >>> converter.to_string(currency, currency('10.5'))
    '$10.50'
"""

import datetime
import gettext
import locale
import re
import sys
import time

from kiwi import ValueUnset
from kiwi.enums import Alignment
from kiwi.python import enum

try:
    from decimal import Decimal, InvalidOperation
    HAVE_DECIMAL = True
    Decimal, InvalidOperation # pyflakes
except:
    HAVE_DECIMAL = False
    class Decimal(float):
        pass
    InvalidOperation = ValueError

if sys.platform == 'win32':
    try:
        import ctypes
        def GetLocaleInfo(value):
            s = ctypes.create_string_buffer("\000" * 255)
            ctypes.windll.kernel32.GetLocaleInfoA(0, value, s, 255)
            return str(s.value)
    except ImportError:
        def GetLocaleInfo(value):
            raise Exception(
                "ctypes is required for datetime types on win32")

__all__ = ['ValidationError', 'lformat', 'converter', 'format_price']

_ = lambda m: gettext.dgettext('kiwi', m)

number = (int, float, long, Decimal)

class ValidationError(Exception):
    pass

class ConverterRegistry:
    def __init__(self):
        self._converters = {}

    def add(self, converter_type):
        """
        Adds converter_type as a new converter
        @param converter_type: a L{BaseConverter} subclass
        """
        if not issubclass(converter_type, BaseConverter):
            raise TypeError("converter_type must be a BaseConverter subclass")

        c = converter_type()
        if c.type in self._converters:
            raise ValueError(converter_type)
        # bool, <type 'bool'>, 'bool'
        self._converters[c.type] = c
        self._converters[str(c.type)] = c
        self._converters[c.type.__name__] = c
        return c
    
    def remove(self, converter_type):
        """
        Removes converter_type from the registry
        @param converter_type: a L{BaseConverter} subclass
        """
        if not issubclass(converter_type, BaseConverter):
            raise TypeError("converter_type must be a BaseConverter subclass")

        ctype = converter_type.type
        if not ctype in self._converters:
            raise KeyError(converter_type)

        del self._converters[ctype]

    def get_converter(self, converter_type):
        try:
            converter = self._converters[converter_type]
        except KeyError:
            # This is a hack:
            # If we're a subclass of enum, create a dynamic subclass on the
            # fly and register it, it's necessary for enum.from_string to work.
            if (issubclass(converter_type, enum) and
                not converter_type in self._converters):
                return self.add(
                    type(enum.__class__.__name__ + 'EnumConverter',
                         (_EnumConverter,), dict(type=converter_type)))
            raise KeyError(converter_type)

        return converter

    def get_converters(self, base_classes=None):
        if base_classes is None:
            return self._converters.values()

        converters = []
        if object in base_classes:
            #: Ugly, but cannot remove from tuple!
            base_classes = list(base_classes)
            base_classes.remove(object)
            base_classes = tuple(base_classes)
            converters.append(self._converters[object])

        for converter in self._converters.values():
            if issubclass(converter.type, base_classes):
                converters.append(converter)

        return converters

    def check_supported(self, data_type):
        converter = self._converters.get(data_type)
        if converter is None:
            supported = ', '.join(map(str, self._converters.keys()))
            raise TypeError(
                "%s is not supported. Supported types are: %s"
                % (data_type, supported))

        return converter.type

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
    @cvar name: The name of the datatype.
    @cvar align: The alignment of the datatype. Normally right for numbers
                 and dates, left for others. Default is left.
    """
    type = None
    name = None
    align = Alignment.LEFT

    def get_compare_function(self):
        """
        This can be overriden by a subclass to provide a custom comparison
        function.
        @returns: cmp
        """
        return cmp

    def as_string(self, value, format):
        """
        Convert the value to a string using the specificed format.
        @param value:
        @param format:
        @returns:
        """

    def from_string(self, value):
        """
        Convert a value from a string.
        @param value:
        @returns:
        """

    def get_mask(self):
        """
        Returns the mask of the entry or None if not specified.
        @returns: the mask or None.
        """
        return None

class _StringConverter(BaseConverter):
    type = str
    name = _('String')

    def as_string(self, value, format=None):
        if format is None:
            format = '%s'
        return format % value

    def from_string(self, value):
        return str(value)

converter.add(_StringConverter)

class _UnicodeConverter(BaseConverter):
    type = unicode
    name = _('Unicode')

    def as_string(self, value, format=None):
        if format is None:
            format = u'%s'
        return format % value

    def from_string(self, value):
        return unicode(value)

converter.add(_UnicodeConverter)

class _IntConverter(BaseConverter):
    type = int
    name = _('Integer')
    align = Alignment.RIGHT

    def as_string(self, value, format=None):
        """Convert a float to a string"""
        if format is None:
            format = '%d'

        # Do not use lformat here, since an integer should always
        # be formatted without thousand separators. Think of the
        # use case of a port number, "3128" is desired, and not "3,128"
        return format % value

    def from_string(self, value):
        "Convert a string to an integer"
        if value == '':
            return ValueUnset

        value = filter_locale(value)
        try:
            return self.type(value)
        except ValueError:
            raise ValidationError(
                _("%s could not be converted to an integer") % value)

converter.add(_IntConverter)

class _LongConverter(_IntConverter):
    type = long
    name = _('Long')
converter.add(_LongConverter)

class _BoolConverter(BaseConverter):
    type = bool
    name = _('Boolean')

    def as_string(self, value, format=None):
        return str(value)

    def from_string(self, value):
        "Convert a string to a boolean"
        if value == '':
            return ValueUnset

        if value.upper() in ('TRUE', '1'):
            return True
        elif value.upper() in ('FALSE', '0'):
            return False

        return ValidationError(
            _("'%s' can not be converted to a boolean") % value)

converter.add(_BoolConverter)

class _FloatConverter(BaseConverter):
    type = float
    name = _('Float')
    align = Alignment.RIGHT

    def as_string(self, value, format=None):
        """Convert a float to a string"""
        format_set = True

        if format is None:
            # From Objects/floatobject.c:
            #
            # The precision (12) is chosen so that in most cases, the rounding noise
            # created by various operations is suppressed, while giving plenty of
            # precision for practical use.
            format = '%.12g'

            format_set = False

        as_str = lformat(format, value)

        # If the format was not set, the resoult should be treated, as
        # follows.
        if not format_set and not value % 1:
            # value % 1 is used to check if value has an decimal part. If it
            # doen't then it's an integer

            # When format is '%g', if value is an integer, the result
            # will also be formated as an integer, so we add a '.0'

            conv = get_localeconv()
            as_str +=  conv.get('decimal_point') + '0'

        return as_str

    def from_string(self, value):
        """Convert a string to a float"""

        if value == '':
            return ValueUnset

        value = filter_locale(value)
        try:
            retval = float(value)
        except ValueError:
            raise ValidationError(_("This field requires a number, not %r") %
                                  value)

        return retval

converter.add(_FloatConverter)

class _DecimalConverter(_FloatConverter):
    type = Decimal
    name = _('Decimal')
    align = Alignment.RIGHT
    def from_string(self, value):
        if value == '':
            return ValueUnset

        value = filter_locale(value)

        try:
            retval = Decimal(value)
        except InvalidOperation:
            raise ValidationError(_("This field requires a number, not %r") %
                                  value)

        return retval

converter.add(_DecimalConverter)

# Constants for use with win32
LOCALE_SSHORTDATE = 31
LOCALE_STIMEFORMAT = 4099
DATE_REPLACEMENTS_WIN32 = [
    (re.compile('HH?'), '%H'),
    (re.compile('hh?'), '%I'),
    (re.compile('mm?'), '%M'),
    (re.compile('ss?'), '%S'),
    (re.compile('tt?'), '%p'),
    (re.compile('dd?'), '%d'),
    (re.compile('MM?'), '%m'),
    (re.compile('yyyyy?'), '%Y'),
    (re.compile('yy?'), '%y')
    ]

# This "table" contains, associated with each
# key (ie. strftime "conversion specifications")
# a tuple, which holds in the first position the
# mask characters and in the second position
# a "human-readable" format, used for outputting user
# messages (see method _BaseDateTimeConverter.convert_format) 
DATE_MASK_TABLE = {
    '%m': ('00', _('mm')),
    '%y': ('00', _('yy')),
    '%d': ('00', _('dd')),
    '%Y': ('0000', _('yyyy')),
    '%H': ('00', _('hh')),
    '%M': ('00', _('mm')),
    '%S': ('00', _('ss')),
    '%T': ('00:00:00', _('hh:mm:ss')),
    # FIXME: locale specific
    '%r': ('00:00:00 LL', _('hh:mm:ss LL')),
    }

class _BaseDateTimeConverter(BaseConverter):
    """
    Abstract class for converting datatime objects to and from strings
    @cvar date_format:
    @cvar lang_constant:
    """
    date_format = None
    align = Alignment.RIGHT

    def __init__(self):
        self._keep_am_pm = False
        self._keep_seconds = False

    def get_lang_constant_win32(self):
        raise NotImplementedError

    def get_lang_constant(self):
        # This is a method and not a class variable since it does not
        # exist on all supported platforms, eg win32
        raise NotImplementedError

    def from_dateinfo(self, dateinfo):
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

    def get_format(self):
        if sys.platform == 'win32':
            values = []
            for constant in self.get_lang_constant_win32():
                value = GetLocaleInfo(constant)
                values.append(value)
            format = " ".join(values)

            # Now replace them to strftime like masks so the logic
            # below still applies
            for pattern, replacement in DATE_REPLACEMENTS_WIN32:
                format = pattern.subn(replacement, format)[0]
        else:
            format = locale.nl_langinfo(self.get_lang_constant())

        format = format.replace('%r', '%I:%M:%S %p')
        format = format.replace('%T', '%H:%M:%S')

        # Strip AM/PM
        if not self._keep_am_pm:
            if '%p' in format:
                format = format.replace('%p', '')
                # 12h -> 24h
                format = format.replace('%I', '%H')

        # Strip seconds
        if not self._keep_seconds:
            if '%S' in format:
                format = format.replace('%S', '')

        # Strip trailing characters
        while format[-1] in ('.', ':', ' '):
            format = format[:-1]

        return format

    def get_mask(self):
        mask = self.get_format()
        for format_char, mask_char in DATE_MASK_TABLE.items():
            mask = mask.replace(format_char, mask_char[0])

        return mask

    def as_string(self, value, format=None):
        "Convert a date to a string"
        if format is None:
            format = self.get_format()

        if value is None:
            return ''

        if isinstance(value, (datetime.date, datetime.datetime)):
            if value.year < 1900:
                raise ValidationError(
                    _("You cannot enter a year before 1900"))

        return value.strftime(format)

    def _convert_format(self, format):
        "Convert the format string to a 'human-readable' format"
        for char in DATE_MASK_TABLE.keys():
            format = format.replace(char, DATE_MASK_TABLE[char][1])

        return format

    def from_string(self, value):
        "Convert a string to a date"

        if value == "":
            return None

        # We're only supporting strptime values for now,
        # perhaps we should add macros, to be able to write
        # yyyy instead of %Y

        format = self.get_format()
        try:
            # time.strptime (python 2.4) does not support %r
            # pending SF bug #1396946
            dateinfo = time.strptime(value, format)
            date = self.from_dateinfo(dateinfo)
        except ValueError:
            raise ValidationError(
                _('This field requires a date of the format "%s" and '
                  'not "%s"') % (self._convert_format(format), value))

        if isinstance(date, (datetime.date, datetime.datetime)):
            if date.year < 1900:
                raise ValidationError(
                    _("You cannot enter a year before 1900"))
        return date


class _TimeConverter(_BaseDateTimeConverter):
    type = datetime.time
    name = _('Time')
    date_format = '%X'
    def get_lang_constant_win32(self):
        return [LOCALE_STIMEFORMAT]

    def get_lang_constant(self):
        return locale.T_FMT

    def from_dateinfo(self, dateinfo):
        # hour, minute, second
        return datetime.time(*dateinfo[3:6])
converter.add(_TimeConverter)

class _DateTimeConverter(_BaseDateTimeConverter):
    type = datetime.datetime
    name = _('Date and Time')
    date_format = '%c'
    def get_lang_constant_win32(self):
        return [LOCALE_SSHORTDATE, LOCALE_STIMEFORMAT]

    def get_lang_constant(self):
        return locale.D_T_FMT

    def from_dateinfo(self, dateinfo):
        # year, month, day, hour, minute, second
        return datetime.datetime(*dateinfo[:6])
converter.add(_DateTimeConverter)

class _DateConverter(_BaseDateTimeConverter):
    type = datetime.date
    name = _('Date')
    date_format = '%x'
    def get_lang_constant_win32(self):
        return [LOCALE_SSHORTDATE]

    def get_lang_constant(self):
        return locale.D_FMT

    def from_dateinfo(self, dateinfo):
        # year, month, day
        return datetime.date(*dateinfo[:3])
converter.add(_DateConverter)

class _ObjectConverter(BaseConverter):
    type = object
    name = _('Object')

    as_string = None
    from_string = None
converter.add(_ObjectConverter)

class _EnumConverter(BaseConverter):
    type = enum
    name = _('Enum')

    def as_string(self, value, format=None):
        if not isinstance(value, self.type):
            raise ValidationError(
                "value must be an instance of %s, not %r" % (
                self.type, value))
        return value.name

    def from_string(self, value):
        names = self.type.names
        if not value in names:
            raise ValidationError(
                "Invalid value %s for enum %s" % (value, self.type))
        return names[value]

converter.add(_EnumConverter)

def lformat(format, value):
    """Like locale.format but with grouping enabled"""
    return locale.format(format, value, 1)

def get_localeconv():
    conv = locale.localeconv()

    monetary_locale = locale.getlocale(locale.LC_MONETARY)
    numeric_locale = locale.getlocale(locale.LC_NUMERIC)
    # Patching glibc's output
    # See http://sources.redhat.com/bugzilla/show_bug.cgi?id=1294
    if monetary_locale[0] == 'pt_BR':
        conv['p_cs_precedes'] = 1
        conv['p_sep_by_space'] = 1

    # Since locale 'C' doesn't have any information on monetary and numeric
    # locale, use default en_US, so we can have formated numbers
    if not monetary_locale[0]:
        conv["negative_sign"] = '-'
        conv["currency_symbol"] = '$'
        conv['mon_thousands_sep'] = ''
        conv['mon_decimal_point'] = '.'
        conv['p_sep_by_space'] = 0

    if not numeric_locale[0]:
        conv['decimal_point'] = '.'

    return conv

def filter_locale(value, monetary=False):
    """
    Removes the locale specific data from the value string.
    Currently we only remove the thousands separator and
    convert the decimal point.
    The returned value of this function can safely be passed to float()

    @param value: value to convert
    @param monetary: if we should treat it as monetary data or not
    @returns: the value without locale specific data
    """

    def _filter_thousands_sep(value, thousands_sep):
        if not thousands_sep:
            return value

        # Check so we don't have any thousand separators to the right
        # of the decimal point
        th_sep_count = value.count(thousands_sep)
        if th_sep_count and decimal_points:
            decimal_point_pos = value.index(decimal_point)
            if thousands_sep in value[decimal_point_pos+1:]:
                raise ValidationError(_("You have a thousand separator to the "
                                        "right of the decimal point"))
            check_value = value[:decimal_point_pos]
        else:
            check_value = value

        # Verify so the thousand separators are placed properly
        # TODO: Use conv['grouping'] for locales where it's not 3
        parts = check_value.split(thousands_sep)

        # First part is a special case, It can be 1, 2 or 3
        if 3 > len(parts[0]) < 1:
            raise ValidationError(_("Inproperly placed thousands separator"))

        # Middle parts should have a length of 3
        for part in parts[1:]:
            if len(part) != 3:
                raise ValidationError(_("Inproperly placed thousand "
                                        "separators: %r" % (parts,)))

        # Remove all thousand separators
        return value.replace(thousands_sep, '')

    conv = get_localeconv()

    # Check so we only have one decimal point
    if monetary:
        decimal_point = conv["mon_decimal_point"]
    else:
        decimal_point = conv["decimal_point"]

    if decimal_point != '':
        decimal_points = value.count(decimal_point)
        if decimal_points > 1:
            raise ValidationError(
                _('You have more than one decimal point ("%s") '
                  ' in your number "%s"' % (decimal_point, value)))

    if monetary:
        sep = conv["mon_thousands_sep"]
    else:
        sep = conv["thousands_sep"]

    if sep and sep in value:
        value = _filter_thousands_sep(value, sep)

    # Replace all decimal points with .
    if decimal_point != '.' and decimal_point != '':
        value = value.replace(decimal_point, '.')
    return value

# FIXME: Get rid of this
from kiwi.currency import currency, format_price

# Pyflakes
currency
format_price
