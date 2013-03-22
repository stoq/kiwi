# encoding: utf-8
import random

import gtk

from kiwi.ui.comboentry import ComboEntry


class Person:
    """The parameters need to be of the same name of the column headers"""
    def __init__(self, name, age, city):
        (self.name, self.age,
         self.city) = name, age, city
        self.salary = random.randint(40, 180) * 10
        self.bonus = random.randint(0, 1) and True or False

data = (Person('Evandro', 23, 'Belo Horizonte'),
        Person('Daniel', 22, 'São Carlos'),
        Person('Henrique', 21, 'São Carlos'),
        Person('Gustavo', 23, 'São Jose do Santos'),
        Person('Johan', 23, 'Göteborg'),
        Person('Lorenzo', 26, 'Granada')
        )


def details_callback(data):
    return "<small><b>city:</b> <span foreground='#0000FF'>%s</span> \n" \
           "<b>age:</b> %s</small>" % (data.city, data.age)

win = gtk.Window()
win.set_position(gtk.WIN_POS_CENTER)
win.connect('destroy', gtk.main_quit)

vbox = gtk.VBox()
win.add(vbox)

e = ComboEntry()
e.set_details_callback(details_callback)

for d in data:
    e.append_item(d.name, d)

vbox.pack_start(e)
win.show_all()

gtk.main()
