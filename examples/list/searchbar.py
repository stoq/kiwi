import gtk

from kiwi.datatypes import currency
from kiwi.ui.objectlist import Column, ObjectList

class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __repr__(self):
        return '<Product %s>' % self.name

columns = [
    Column('name', data_type=str),
    Column('price', data_type=currency, sorted=True),
    ]

data = (Product('Snacks', '3.50'),
        Product('Juice', '4.75'),
        Product('Apple', '0.35'),
        Product('Chocolate bar', '8.5'),
        Product('Bubble gum', '0.3'),
        Product('Tutti-frutti', '1.50')
       )

win = gtk.Window()
win.connect('destroy', gtk.main_quit)
win.set_border_width(6)
win.set_size_request(650, 300)

vbox = gtk.VBox()
win.add(vbox)

def entry_activate_cb(entry):
    text = entry.get_text()
    products = [product for product in data
                            if text.lower() in product.name.lower()]
    l.add_list(products)

entry = gtk.Entry()
entry.connect('activate', entry_activate_cb)
vbox.pack_start(entry, False, False, 6)

l = ObjectList(columns)
l.extend(data)
vbox.pack_start(l)

win.show_all()

gtk.main()
