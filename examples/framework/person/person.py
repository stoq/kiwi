#!/usr/bin/env python
import gtk
from kiwi.model import PickledModel
from kiwi.ui.delegates import ProxyDelegate

# define the class that holds our application data


class Person(PickledModel):
    pass
person = Person.unpickle()

# create and run a proxy interface attached to person
view = ProxyDelegate(person, gladefile="Person.ui",
                     widgets=["address", 'name', 'phone'],
                     delete_handler=gtk.main_quit)
view.focus_topmost()
view.show_and_loop()

# save changes done to the instance
person.save()
