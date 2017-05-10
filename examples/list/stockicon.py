from gi.repository import Gtk

from kiwi.ui.objectlist import Column, ObjectList


class Fruit:
    def __init__(self, icon, name):
        self.icon = icon
        self.name = name

fruits = ObjectList([Column('icon', use_stock=True,
                            justify=Gtk.Justification.CENTER,
                            icon_size=Gtk.IconSize.LARGE_TOOLBAR),
                     Column('name', column='icon')])

for icon, name in [(Gtk.STOCK_OK, 'Apple'),
                   (Gtk.STOCK_CANCEL, 'Pineapple'),
                   (Gtk.STOCK_HELP, 'Kiwi'),
                   (Gtk.STOCK_DELETE, 'Banana'),
                   (Gtk.STOCK_HOME, 'Melon')]:
    fruits.append(Fruit(icon, name))

window = Gtk.Window()
window.connect('delete-event', Gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(150, 180)

window.add(fruits)
window.show_all()

Gtk.main()
