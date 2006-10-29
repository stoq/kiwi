import gtk

from kiwi.python import enum
from kiwi.ui.objectlist import Column, ObjectList

class FruitStatus(enum):
    (AVAILABLE,
     SOLD_OUT,
     ROTTEN) = range(3)

class Fruit:
    def __init__(self, name, status):
        self.name = name
        self.status = status

fruits = ObjectList([Column('name', data_type=str),
                     Column('status', title="Current status",
                            data_type=FruitStatus, editable=True)])

for name, status in [('Apple', FruitStatus.AVAILABLE),
                     ('Pineapple', FruitStatus.SOLD_OUT),
                     ('Kiwi', FruitStatus.AVAILABLE),
                     ('Banana', FruitStatus.ROTTEN),
                     ('Melon', FruitStatus.AVAILABLE)]:
    fruits.append(Fruit(name, status))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(200, 180)

window.add(fruits)
window.show_all()

gtk.main()
