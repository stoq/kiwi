from datetime import date, datetime, time
import random

import gtk

from kiwi.ui.widgets.list import Column, List, SequentialColumn

def random_date():
    max = datetime.today()
    min = max.replace(year=max.year-5)
    timestamp = random.randint(int(min.strftime('%s')),
                               int(max.strftime('%s')))
    return datetime.fromtimestamp(timestamp)
    
class Person:
    """The parameters need to be of the same name of the column headers"""
    def __init__(self, name, age, city, present):
        (self.name, self.age,
         self.city, self.present) = name, age, city, present
        self.date = self.datetime = self.time = random_date()

    def __repr__(self):
        return '<Person %s>' % self.name

class MyColumn(Column):
    pass

def format_func(age):
    if age % 2 == 0:
        return float(age)
    return age

columns = [
    SequentialColumn(),
    MyColumn('name', tooltip='What about a stupid tooltip?', editable=True),
    Column('age', format_func=format_func, editable=True),
    Column('city', visible=True, sorted=True),
    Column('date', data_type=date),
    Column('time', data_type=time),
    Column('datetime', data_type=datetime),
    ]

data = (Person('Evandro', 23, 'Belo Horizonte', True),
        Person('Daniel', 22, 'Sao Carlos', False),
        Person('Henrique', 21, 'Sao Carlos', True),
        Person('Gustavo', 23, 'San Jose do Santos', False),
        Person('Johan', 23, 'Goteborg', True), 
        Person('Lorenzo', 26, 'Granada', False)
    )

win = gtk.Window()
win.set_default_size(500, 150)
win.connect('destroy', gtk.main_quit)

l = List(columns, data)
l.add_list([Person('Nando', 29+len(l), 'Santos', True)], False)

# add an extra person

win.add(l)
win.show_all()

gtk.main()

