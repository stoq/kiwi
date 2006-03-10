import gtk

from kiwi.ui.objectlist import Column, ObjectList

class Fruit:
    def __init__(self, name, cost):
        self.name = name
        self.cost = cost

fruits = ObjectList([Column('name', data_type=str, editable=True,
                      expand=True),
               Column('cost', data_type=int, editable=True)])

for name, cost in [('Apple', 4),
                   ('Pineapple', 2),
                   ('Kiwi', 8),
                   ('Banana', 3),
                   ('Melon', 5)]:
    fruits.append(Fruit(name, cost))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Editable Fruit List')
window.set_size_request(230, 150)

window.add(fruits)
window.show_all()

gtk.main()
