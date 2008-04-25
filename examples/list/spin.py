import gtk

from kiwi.ui.objectlist import Column, ObjectList

class Fruit:
    def __init__(self, name, status):
        self.name = name
        self.status = status

adjustment = gtk.Adjustment(step_incr=1, upper=15)
fruits = ObjectList([Column('name', data_type=str),
                     Column('quantity', title="Quantity",
                            spin_adjustment=adjustment, data_type=float,
                            editable=True)])
fruits.set_spinbutton_digits('quantity', 3)

for name, quantity in [('Apple', 1),
                     ('Pineapple', 2),
                     ('Kiwi', 3),
                     ('Banana', 4),
                     ('Melon', 6)]:
    fruits.append(Fruit(name, quantity))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(200, 180)

window.add(fruits)
window.show_all()

gtk.main()
