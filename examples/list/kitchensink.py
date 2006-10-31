# encoding: utf-8
import datetime
import random
import time

import gtk

from kiwi.datatypes import currency
from kiwi.ui.objectlist import (Column, ObjectList, SequentialColumn,
                                  ColoredColumn, SummaryLabel)

def random_date():
    max = datetime.datetime.today()
    min = max.replace(year=max.year-5)

    timestamp = random.randint(
        time.mktime(min.timetuple()),
        time.mktime(max.timetuple()))
    return datetime.datetime.fromtimestamp(timestamp)

class Person:
    """The parameters need to be of the same name of the column headers"""
    def __init__(self, name, age, city):
        (self.name, self.age,
         self.city) = name, age, city
        self.date = self.datetime = self.time = random_date()
        self.extra = -1
        self.salary = random.randint(40, 180) * 10
        self.bonus = random.randint(0, 1) and True or False

    def __repr__(self):
        return '<Person %s>' % self.name

class MyColumn(Column):
    pass

def format_func(age):
    if age % 2 == 0:
        return float(age)
    return age

def color(data):
    return data % 2 == 0

columns = [
    SequentialColumn(),
    MyColumn('name', tooltip='What about a stupid tooltip?', editable=True),
    Column('age', data_type=int, format_func=format_func, editable=True),
    Column('bonus', data_type=bool, editable=True),
    Column('salary', data_type=currency, editable=True),
    Column('city', visible=True, sorted=True),
    Column('date', data_type=datetime.date),
    Column('time', data_type=datetime.time),
    Column('datetime', data_type=datetime.datetime),
    ColoredColumn('age', data_type=int, color='red', data_func=color),
    ]

data = (Person('Evandro', 23, 'Belo Horizonte'),
        Person('Daniel', 22, 'São Carlos'),
        Person('Henrique', 21, 'São Carlos'),
        Person('Gustavo', 23, 'São Jose do Santos'),
        Person('Johan', 23, 'Göteborg'),
        Person('Lorenzo', 26, 'Granada')
       )

win = gtk.Window()
win.set_size_request(850, 300)
win.connect('destroy', gtk.main_quit)

vbox = gtk.VBox()
win.add(vbox)

l = ObjectList(columns, mode=gtk.SELECTION_MULTIPLE)
l.extend(data)
l.append(Person('Nando', 29+len(l), 'Santos'))


# add an extra person

vbox.pack_start(l)

label = SummaryLabel(klist=l, column='salary', label='<b>Total:</b>',
                     value_format='<b>%s</b>')
vbox.pack_start(label, expand=False, padding=6)

win.show_all()

gtk.main()
