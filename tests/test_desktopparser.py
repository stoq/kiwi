# encoding: utf-8
import StringIO
import unittest

from kiwi.desktopparser import DesktopParser

desktop_data = """
[Desktop Entry]
Name=Totem Movie Player
Name[pt]=Reprodutor de Filmes Totem
Name[sv]=Filmspelaren Totem
Categories=GNOME;Application;AudioVideo
"""


class TestTotem(unittest.TestCase):
    def setUp(self):
        self.parser = DesktopParser()
        self.parser.readfp(StringIO.StringIO(desktop_data))

    def test(self):
        self.assertEqual(self.parser.get('Desktop Entry', 'Name'),
                         'Totem Movie Player')
        self.assertEqual(self.parser.get_locale(
            'Desktop Entry', 'Name', 'pt'), 'Reprodutor de Filmes Totem')
        self.assertEqual(self.parser.get_locale(
            'Desktop Entry', 'Name', 'sv'), 'Filmspelaren Totem')
        self.assertEqual(
            self.parser.get_string_list('Desktop Entry', 'Categories'),
            ['GNOME', 'Application', 'AudioVideo'])


class TestDesktopParser(unittest.TestCase):
    def setUp(self):
        self.parser = DesktopParser()
        self.parser.add_section('Section')

    def testList(self):
        self.parser.set_string_list('Section', 'Foo', ['A', 'B', 'C'])
        self.assertEqual(
            self.parser.get_string_list('Section', 'Foo'),
            ['A', 'B', 'C'])

        self.parser.set_integer_list('Section', 'Bar', [1, 2, 3])
        self.assertEqual(
            self.parser.get_integer_list('Section', 'Bar'),
            [1, 2, 3])

        self.parser.set_boolean_list('Section', 'Bar', [True, False])
        self.assertEqual(
            self.parser.get_boolean_list('Section', 'Bar'),
            [True, False])

    def testLocale(self):
        self.parser.set_locale(
            'Section', 'Foo', 'sv', 'Apa')
        self.assertEqual(
            self.parser.get_locale('Section', 'Foo', 'sv'),
            'Apa')

        self.parser.set_string_list_locale(
            'Section', 'Foo', 'sv', ['å', 'ä', 'ö'])
        self.assertEqual(
            self.parser.get_string_list_locale('Section', 'Foo', 'sv'),
            ['å', 'ä', 'ö'])

    def testListSeparator(self):
        self.parser.set('Section', 'Comma', '1,2,3')
        self.assertEqual(
            self.parser.get_string_list('Section', 'Comma'),
            ['1,2,3'])
        self.parser.set_list_separator(',')
        self.assertEqual(
            self.parser.get_string_list('Section', 'Comma'),
            ['1', '2', '3'])
