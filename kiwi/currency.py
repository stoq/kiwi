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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""Currency and datatype converter"""

import gettext

from kiwi.datatypes import HAVE_DECIMAL, Decimal, InvalidOperation
from kiwi.datatypes import ValidationError, ValueUnset
from kiwi.datatypes import converter, get_localeconv, filter_locale
from kiwi.enums import Alignment

_ = lambda m: gettext.dgettext('kiwi', m)

class currency(Decimal):
    """
    A datatype representing currency, used together with the list and
    the framework
    """
    _converter = converter.get_converter(Decimal)

    def __new__(cls, value):
        """
        Convert value to currency.
        @param value: value to convert
        @type value: string or number
        """
        if isinstance(value, str):
            conv = get_localeconv()
            currency_symbol = conv.get('currency_symbol')
            text = value.strip(currency_symbol)
            # if we cannot convert it using locale information, still try to
            # create
            try:
                text = filter_locale(text, monetary=True)
                value = currency._converter.from_string(text)
            except ValidationError:
                # Decimal does not accept leading and trailing spaces. See
                # bug 1516613
                value = text.strip()

            if value == ValueUnset:
                raise InvalidOperation
        elif HAVE_DECIMAL and isinstance(value, float):
            print ('Warning: losing precision converting float %r to currency'
                   % value)
            value = str(value)
        elif not isinstance(value, (int, long, Decimal)):
            raise TypeError(
                "cannot convert %r of type %s to a currency" % (
                value, type(value)))

        return Decimal.__new__(cls, value)

    def format(self, symbol=True, precision=None):
        value = Decimal(self)

        conv = get_localeconv()

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

            format = '%%.%sf' % (frac_digits+1)
            dec_part = (format % value)[-(frac_digits+1):-1]

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
        return '<currency %s>' % self.format()

_DecimalConverter = type(converter.get_converter(Decimal))

class _CurrencyConverter(_DecimalConverter):
    type = currency
    name = _('Currency')
    align = Alignment.RIGHT

    def __init__(self):
        self.symbol = True
        self.precision = 2

    def as_string(self, value, format=None, symbol=None, precision=None):
        if value == ValueUnset:
            return ''

        if not isinstance(value, currency):
            try:
                value = currency(value)
            except ValueError:
                raise ValidationError(
                    _("%s can not be converted to a currency") % value)

        if symbol is None:
            symbol = self.symbol

        if precision is None:
            precision = self.precision

        return value.format(symbol, precision)

    def from_string(self, value):
        if value == '':
            return ValueUnset
        try:
            return currency(value)
        except (ValueError, InvalidOperation):
            raise ValidationError(
                _("%s can not be converted to a currency") % value)

converter.add(_CurrencyConverter)


def format_price(value, symbol=True, precision=None):
    """
    Formats a price according to the current locales monetary
    settings

    @param value: number
    @param symbol: whether to include the currency symbol
    """

    return currency(value).format(symbol, precision)
