import gtk
from kiwi.ui.objectlist import Column, ObjectList

class Object:
    def __init__(self, name, value):
        self.name, self.value = name, value

columns = [Column('name'),
           Column('value', data_type=bool, radio=True, editable=True)]

win = gtk.Window()
win.set_size_request(300, 120)
win.connect('delete-event', gtk.main_quit)

list = ObjectList(columns)
win.add(list)

for name, value in [('First', False),
                    ('Second', False),
                    ('Third', True),
                    ('Fourth', False),
                    ('Fifth', False)]:
    list.append(Object(name, value))
win.show_all()

gtk.main()
