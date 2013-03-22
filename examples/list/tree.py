import gtk

from kiwi.ui.objectlist import Column, ObjectTree


class Fruit:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class FruitDesc:
    def __init__(self, name):
        self.name = name

fruits = ObjectTree([Column('name', data_type=str),
                     Column('price', data_type=int)])

for name, price in [('Apple', 4),
                    ('Pineapple', 2),
                    ('Kiwi', 8),
                    ('Banana', 3),
                    ('Melon', 5)]:
    row = fruits.append(None, FruitDesc(name))
    fruits.append(row, Fruit('Before taxes', price * 0.25))
    fruits.append(row, Fruit('After taxes', price))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(150, 180)

window.add(fruits)
window.show_all()

gtk.main()
