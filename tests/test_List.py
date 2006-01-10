#!/usr/bin/env python
import unittest

import gtk

from kiwi.ui.widgets.list import List, Column
from utils import refresh_gui

class Person:
    def __init__(self, name, age):
        self.name, self.age = name, age        

# we will use this tuple in several tests
persons = (Person('Johan', 24), Person('Gustavo', 25),
           Person('Kiko', 28), Person('Salgado', 25),
           Person('Lorenzo', 26), Person('Henrique', 21))

class ColumnTests(unittest.TestCase):

    def setUp(self):
        self.win = gtk.Window()
        self.win.set_default_size(400, 400)

    def tearDown(self):
        self.win.destroy()
        del self.win

    def testEmptyList(self):
        mylist = List()
        self.win.add(mylist)
        refresh_gui()

    def testOneColumn(self):
        # column's attribute can not contain spaces
        self.assertRaises(AttributeError, Column, 'test column')
        
        mylist = List(Column('test_column'))
        self.win.add(mylist)
        refresh_gui()

        self.assertEqual(1, len(mylist.get_columns()))
        
class DataTests(unittest.TestCase):
    """In all this tests we use the same configuration for a list"""
    def setUp(self):
        self.win = gtk.Window()
        self.win.set_default_size(400, 400)
        self.list = List([Column('name'), Column('age')])
        self.win.add(self.list)
        refresh_gui()

    def tearDown(self):
        self.win.destroy()
        del self.win

    def testAddingOneInstance(self):
        # we should have two columns now
        self.assertEqual(2, len(self.list.get_columns()))
                         
        person = Person('henrique', 21)
        self.list.append(person)

        refresh_gui()

        # usually you don't use the model directly, but tests are all about
        # breaking APIs, right?
        self.assertEqual(self.list[0], person)
        self.assertEqual(self.list[0].name, 'henrique')
        self.assertEqual(self.list[0].age, 21)

        # we still have to columns, right?
        self.assertEqual(2, len(self.list.get_columns()))

    def testAddingAList(self):
        global persons

        self.list.add_list(persons)
        refresh_gui()
        
        self.assertEqual(len(self.list), len(persons))
        
    def testAddingABunchOfInstances(self):
        global persons

        for person in persons:
            self.list.append(person)
            refresh_gui()

        self.assertEqual(len(self.list), len(persons))

    def testRemovingOneInstance(self):
        global  persons

        self.list.add_list(persons)
        refresh_gui()

        # we are going to remove Kiko
        person = persons[2]

        self.list.remove(person)

        self.assertEqual(len(self.list), len(persons) - 1)

        # now let's remove something that is not on the list
        #new_person = Person('Evandro', 24)
        #self.assertRaises(ValueError, self.list.remove, new_person)

        # note that even a new person with the same values as a person
        # in the list is not considered to be in the list
        #existing_person = Person('Gustavo', 25)
        #self.assertRaises(ValueError, self.list.remove,
        #                  existing_person)

    def testClearList(self):
        global persons

        self.list.add_list(persons)
        refresh_gui()

        self.list.clear()

        self.assertEqual(len(self.list), 0)
        

    def testUpdatingOneInstance(self):
        global persons

        self.list.add_list(persons)
        refresh_gui()

        persons[0].age = 29
        self.list.update(persons[0])

        refresh_gui()
        
        # Do we have the same number of instances that we had before ?
        self.assertEqual(len(self.list), len(persons))

        # Trying to find our updated instance in the list
        self.assertEqual(self.list[0].age, 29)

        # let's be evil
        new_person = Person('Nando', 32)
        self.assertRaises(ValueError, self.list.update, new_person)


    def testContains(self):
        global persons

        self.list.add_list(persons)
        self.assertEqual(persons[0] in self.list, True)

        new_person = Person('Nando', 32)
        self.assertEqual(new_person in self.list, False)

    def testSelect(self):
        first = persons[0]
        self.list.add_list(persons)
        self.list.select(first)
        self.assertEqual(self.list.get_selected(), first)

        self.list.remove(first)
        self.assertRaises(ValueError, self.list.select, first)
        
if __name__ == '__main__':
    unittest.main()
