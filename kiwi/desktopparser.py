#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006 Johan Dahlin <jdahlin@async.com.br>
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
# Based on gkeyfile.c from glib, written by
#
#   Ray Strode <rstrode@redhat.com>
#   Matthias Clasen <mclasen@redhat.com>
#

from ConfigParser import ConfigParser, NoOptionError

# Private


def _localize(option, locale):
    if locale:
        option = option + '[%s]' % locale
    return option


def _tobool(s):
    if s == 'true':
        return True
    return False


def _frombool(s):
    if s:
        return 'true'
    return 'false'


class DesktopParser(ConfigParser):
    """
    A DesktopParser for GNOME/KDE .desktop files.
    The API is similar to GKeyFile from glib.

    Example:

    >>> parser = DesktopParser()
    >>> parser.read('/usr/share/applications/gnome-terminal.desktop')
    >>> parser.get_locale('Desktop Entry', 'Comment', 'pt')
    """
    def __init__(self, defaults=None):
        ConfigParser.__init__(self, defaults)
        self._list_separator = ';'

    # ConfigParser overrides

    def optionxform(self, optionstr):
        # .desktop files are case sensitive
        # The default implementation makes it lowercase,
        # so override to just use it as it was read
        return optionstr

    # Public

    def set_list_separator(self, separator):
        """
        Sets the character which is used to separate
        values in lists. Typically ';' or ',' are used
        as separators. The default list separator is ';'.

        :param separator: the separator
        """
        self._list_separator = separator

    def set_locale(self, section, option, locale, value):
        """
        Set locale.

        :param section: section name
        :param option: an option
        :param locale: a locale
        :param value: value to set
        """
        self.set(section, _localize(option, locale), value)

    def get_locale(self, section, option, locale):
        """
        Get locale.

        :param section: section name
        :param option: an option
        :param locale: a locale
        """
        try:
            return self.get(section, _localize(option, locale))
        except NoOptionError:
            # Fallback to default option
            return self.get(section, option)

    def get_string_list(self, section, option):
        """
        Get a list as string.

        :param section: section name
        :param option: an option
        """
        return self.get(section, option).split(self._list_separator)

    def set_string_list(self, section, option, values):
        """
        Set a list of string values.

        :param section: section name
        :param option: an option
        :param values: list of string values
        """
        value = self._list_separator.join(values)
        self.set(section, option, value)

    def get_integer_list(self, section, option):
        """
        Get a list of integers as string.

        :param section: section name
        :param option: an option
        """
        return map(int, self.get_string_list(section, option))

    def set_integer_list(self, section, option, values):
        """
        Set a list with integer values.

        :param section: section name
        :param option: an option
        :param values: list of integer values
        """
        self.set_string_list(section, option, map(str, values))

    def get_boolean_list(self, section, option):
        """
        Get a boolean list.

        :param section: section name
        :param option: an option
        """
        return map(_tobool, self.get_string_list(section, option))

    def set_boolean_list(self, section, option, values):
        """
        Set an list wiht boolena values.

        :param section: section name
        :param option: an option
        :param values: list of boolean values
        """
        self.set_string_list(section, option, map(_frombool, values))

    def set_string_list_locale(self, section, option, locale, values):
        """
        Set string list with locale values.

        :param section: section name
        :param option: an option
        :param locale: a locale
        :param values: list of string values
        """
        self.set_string_list(section, _localize(option, locale), values)

    def get_string_list_locale(self, section, option, locale):
        """
        Get list locale as an string.

        :param section: section name
        :param option: an option
        :param locale: a locale
        """
        try:
            return self.get_string_list(section, _localize(option, locale))
        except NoOptionError:
            # Fallback to default option
            return self.get_string_list(section, option)
