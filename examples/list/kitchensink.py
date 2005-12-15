from datetime import date, datetime, time
import random

import gtk

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import (Column, List, SequentialColumn,
                                  ColoredColumn, SummaryLabel)

def random_date():
    max = datetime.today()
    min = max.replace(year=max.year-5)
    timestamp = random.randint(int(min.strftime('%s')),
                               int(max.strftime('%s')))
    if timestamp % 2 == 0:
        return 
    return datetime.fromtimestamp(timestamp)
    
class Person:
    """The parameters need to be of the same name of the column headers"""
    def __init__(self, name, age, city):
        (self.name, self.age,
         self.city) = name, age, city
        self.date = self.datetime = self.time = random_date()
        self.extra = -1
        self.worth = random.randint(0, 10000) / 100.0
        self.bool = random.randint(0, 1) and True or False
        
    def __repr__(self):
        return '<Person %s>' % self._name

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
    Column('age', format_func=format_func, editable=True, width=40),
    Column('bool', data_type=bool, editable=True, width=40),
    Column('worth', data_type=currency, editable=True),
    Column('city', visible=True, sorted=True),
    Column('date', data_type=date),
    Column('time', data_type=time),
    Column('datetime', data_type=datetime),
    ColoredColumn('age', data_type=int, color='red', data_func=color),
    ]

data = (Person('Evandro', 23, 'Belo Horizonte'),
        Person('Daniel', 22, 'Sao Carlos'),
        Person('Henrique', 21, 'Sao Carlos'),
        Person('Gustavo', 23, 'San Jose do Santos'),
        Person('Johan', 23, 'Goteborg'), 
        Person('Lorenzo', 26, 'Granada')
       )

win = gtk.Window()
win.set_size_request(650, 300)
win.connect('destroy', gtk.main_quit)

vbox = gtk.VBox()
win.add(vbox)

l = List(columns)
l.extend(data)
l.append(Person('Nando', 29+len(l), 'Santos'))


# add an extra person

vbox.pack_start(l)

label = SummaryLabel(klist=l, column='age', label='<b>Total:</b>',
                     value_format='<b>%s</b>')
vbox.pack_start(label, expand=False, padding=6)

win.show_all()

gtk.main()

