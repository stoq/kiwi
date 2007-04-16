import gtk

from kiwi.ui.objectlist import Column, ObjectList

class Fruit:
    def __init__(self, name, price):
        self.name = name
        self.price = price

fruits = ObjectList([Column('name', data_type=str, sorted=True),
               Column('price', data_type=int)])

for name, price in [('Kiwi', 8),
                    ('Apple', 4),
                    ('Pineapple', 2),
                    ('Banana', 3),
                    ('Melon', 5)]:
    fruits.append(Fruit(name, price))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(150, 180)

window.add(fruits)
window.show_all()

gtk.main()
