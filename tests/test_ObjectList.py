#!/usr/bin/env python
import unittest

import gobject
import gtk

from kiwi.ui.objectlist import ObjectList, ObjectTree, Column
from kiwi.python import Settable

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

    def testEmptyObjectList(self):
        mylist = ObjectList()
        self.win.add(mylist)
        refresh_gui()

    def testOneColumn(self):
        # column's attribute can not contain spaces
        self.assertRaises(AttributeError, Column, 'test column')

        mylist = ObjectList(Column('test_column'))
        self.win.add(mylist)
        refresh_gui()

        self.assertEqual(1, len(mylist.get_columns()))

    def testAttribute(self):
        column = Column('foo')
        self.assertEquals(column.attribute, "foo")

    def testGObjectNew(self):
        column = gobject.new(Column, attribute='foo')
        self.assertEquals(column.attribute, "foo")

class DataTests(unittest.TestCase):
    """In all this tests we use the same configuration for a list"""
    def setUp(self):
        self.win = gtk.Window()
        self.win.set_default_size(400, 400)
        self.list = ObjectList([Column('name'), Column('age')])
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

    def testAddingAObjectList(self):
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

    def testClearObjectList(self):
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

class TreeDataTests(unittest.TestCase):
    def setUp(self):
        self.win = gtk.Window()
        self.win.set_default_size(400, 400)
        self.tree = ObjectTree([Column('name'), Column('age')])
        self.win.add(self.tree)
        refresh_gui()

    def tearDown(self):
        self.win.destroy()
        del self.win

    def testGetRoot(self):
        root = Person('Big Kahuna', 7000)
        child1 = Person('Craf Kahuna', 200)
        child2 = Person('Sorcerer Kahuna', 150)

        self.tree.append(None, root)
        self.tree.append(root, child1)
        self.tree.append(root, child2)

        test_root = self.tree.get_root(child1)
        self.assertEqual(test_root, root)
        test_root = self.tree.get_root(child2)
        self.assertEqual(test_root, root)
        test_root = self.tree.get_root(root)
        self.assertEqual(test_root, root)

    def testGetDescendants(self):
        root = Person('Big Kahuna', 7000)
        child1 = Person('Craf Kahuna', 200)
        child2 = Person('Sorcerer Kahuna', 150)

        self.tree.append(None, root)
        self.tree.append(root, child1)
        self.tree.append(child1, child2)

        test_descendants = self.tree.get_descendants(root)
        self.assertTrue(child1 in test_descendants)
        self.assertTrue(child2 in test_descendants)
        test_descendants = self.tree.get_descendants(child1)
        self.assertEqual(test_descendants, [child2])
        test_descendants = self.tree.get_descendants(child2)
        self.assertEqual(test_descendants, [])

class TestSignals(unittest.TestCase):
    def setUp(self):
        self.klist = ObjectList()
        self.klist.connect('has-rows', self._on_klist__has_rows)
        self.klist.connect('selection-changed',
                           self._on_klist__selection_changed)
        self.rows = None
        self.selected = None

    def _on_klist__has_rows(self, klist, rows):
        self.rows = rows

    def _on_klist__selection_changed(self, klist, selected):
        self.selected = selected

    def testHasRows(self):
        self.assertEqual(self.rows, None)
        self.assertEqual(len(self.klist), 0)

        # Add one
        self.klist.append(0)
        self.assertEqual(len(self.klist), 1)
        self.assertEqual(self.rows, True)
        self.klist.remove(0)
        self.assertEqual(self.rows, False)
        self.assertEqual(len(self.klist), 0)

        # Add several
        self.klist.extend((1, 2))
        self.assertEqual(len(self.klist), 2)
        self.assertEqual(self.rows, True)
        self.klist.remove(1)
        self.assertEqual(self.rows, True)
        self.klist.remove(2)
        self.assertEqual(self.rows, False)
        self.assertEqual(len(self.klist), 0)

    def testSelectionChanged(self):
        self.assertEqual(self.selected, None)
        self.assertEqual(len(self.klist), 0)
        self.klist.extend((0, 1))
        self.klist.select(0)
        self.assertEqual(self.selected, 0)
        self.klist.unselect_all()
        self.assertEqual(self.selected, None)
        self.assertRaises(ValueError, self.klist.select, 2)

class ConstructorTest(unittest.TestCase):
    def testInvalidArguments(self):
        self.assertRaises(TypeError, ObjectList, columns='')
        self.assertRaises(TypeError, ObjectList, mode='')

    def testInstanceObjectList(self):
        klist = ObjectList([Column('name', sorted=True)],
                     [Settable(name='first')])
        columns = klist.get_columns()
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].attribute, 'name')

    def testInstanceObjectListWithNoneData(self):
        klist = ObjectList([Column('name', sorted=True)],
                     [Settable(name=None)])
        columns = klist.get_columns()
        self.assertEqual(len(columns), 1)

    def testGObjectNew(self):
        olist = gobject.new(ObjectList)
        self.assertTrue(isinstance(olist, ObjectList))

class MethodTest(unittest.TestCase):
    def setUp(self):
        self.klist = ObjectList([Column('name', sorted=True)],
                                [Settable(name='first')])

    def testNonZero(self):
        self.assertEqual(self.klist.__nonzero__(), True)
        self.klist.remove(self.klist[0])
        self.assertEqual(self.klist.__nonzero__(), True)
        if not self.klist:
            raise AssertionError

    def testIter(self):
        for item1 in self.klist:
            pass
        for item2 in iter(self.klist):
            self.assertEqual(item1, item2)

    def testGetItem(self):
        self.klist.append(Settable(name='second'))
        model = self.klist.get_model()
        item1 = model[0][0]
        item2 = model[1][0]
        self.assertEqual(self.klist[0], item1)
        self.assertEqual(self.klist[:1], [item1])
        self.assertEqual(self.klist[-1:], [item2])
        self.assertRaises(TypeError, self.klist.__getitem__, None)

    def testSetItem(self):
        self.klist[0] = Settable(name='second')
        self.assertRaises(NotImplementedError, self.klist.__setitem__,
                          slice(0), None)
        self.assertRaises(TypeError, self.klist.__setitem__, None, None)

    def testIndex(self):
        self.assertRaises(NotImplementedError, self.klist.index, 0, start=0)
        self.assertRaises(NotImplementedError, self.klist.index, 0, stop=0)

        self.assertEqual(self.klist.index(self.klist[0]), 0)
        self.assertRaises(ValueError, self.klist.index, None)

    def testCount(self):
        item = self.klist[0]
        self.assertEqual(self.klist.count(item), 1)
        self.klist.append(item)
        self.assertEqual(self.klist.count(item), 2)
        self.klist.clear()
        self.assertEqual(self.klist.count(item), 0)

    def testPop(self):
        self.assertRaises(NotImplementedError, self.klist.pop, None)

    def testReverse(self):
        self.assertRaises(NotImplementedError, self.klist.reverse, 1, 2)

    def testSort(self):
        self.assertRaises(NotImplementedError, self.klist.sort, 1, 2)

    def testSelectPath(self):
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_NONE)
        self.assertRaises(TypeError, self.klist.select_paths, (0,))
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.klist.select_paths((0,))

    def testSelect(self):
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_NONE)
        self.assertRaises(TypeError, self.klist.select, None)
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_SINGLE)

    def testGetSelected(self):
        item = self.klist[0]
        self.klist.select(item)
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.assertEqual(self.klist.get_selected(), item)

    def testGetSelectedRows(self):
        self.klist.get_treeview().get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        item = self.klist[0]
        self.klist.select(item)
        self.assertEqual(self.klist.get_selected_rows(), [item])

    def testGetNextAndPrevious(self):
        self.klist.append(Settable(name='second'))
        self.klist.append(Settable(name='third'))
        item1, item2, item3 = self.klist

        self.assertEqual(self.klist.get_next(item1), item2)
        self.assertEqual(self.klist.get_next(item2), item3)
        self.assertEqual(self.klist.get_next(item3), item1)
        self.assertRaises(ValueError, self.klist.get_next, None)

        self.assertEqual(self.klist.get_previous(item1), item3)
        self.assertEqual(self.klist.get_previous(item2), item1)
        self.assertEqual(self.klist.get_previous(item3), item2)
        self.assertRaises(ValueError, self.klist.get_previous, None)

    def testInsert(self):
        self.klist = ObjectList([Column('name')])
        self.assertEqual(list(self.klist), [])

        self.klist.insert(0, Settable(name='one'))
        self.assertEqual(self.klist[0].name, 'one')

        self.klist.insert(0, Settable(name='two'))
        self.assertEqual(self.klist[0].name, 'two')
        self.assertEqual(self.klist[1].name, 'one')

        self.klist.insert(1, Settable(name='three'))
        self.assertEqual(self.klist[0].name, 'two')
        self.assertEqual(self.klist[1].name, 'three')
        self.assertEqual(self.klist[2].name, 'one')

class BooleanDataTests(unittest.TestCase):
    def setUp(self):
        self.list = ObjectList([Column('value', data_type=bool, radio=True,
                                editable=True)])
        self.list.append(Settable(value=True))
        self.list.append(Settable(value=False))

    def testAddingInstances(self):
        self.assertEqual(self.list[0].value, True)
        self.assertEqual(self.list[1].value, False)

    def testSelect(self):
        self.assertEqual(self.list[0].value, True)
        self.assertEqual(self.list[1].value, False)

        column = self.list.get_column_by_name('value')
        treeview_column = self.list.get_treeview_column(column)
        renderer = treeview_column.get_cell_renderers()
        renderer[0].emit('toggled', 1)

        self.assertEqual(self.list[0].value, False)
        self.assertEqual(self.list[1].value, True)
        renderer[0].emit('toggled', 0)

        self.assertEqual(self.list[0].value, True)
        self.assertEqual(self.list[1].value, False)


class RadioColumnTests(unittest.TestCase):

    def testRadioWithoutTrue(self):
        olist = ObjectList(
            [Column('foo', radio=True, data_type=bool, editable=True)])
        column = olist.get_treeview().get_column(0)
        renderer = column.get_cell_renderers()[0]

        items = [Settable(foo=False) for i in range(5)]
        olist.add_list(items)

        self.assertEqual(items[0].foo, False)
        renderer.emit('toggled', 0)
        self.assertEqual(items[0].foo, True)


if __name__ == '__main__':
    unittest.main()
