import gtk

from kiwi.ui.objectlist import Column, ObjectList

class Fruit:
    def __init__(self, icon, name):
        self.icon = icon
        self.name = name

fruits = ObjectList([Column('icon', use_stock=True,
                            justify=gtk.JUSTIFY_CENTER,
                            icon_size=gtk.ICON_SIZE_LARGE_TOOLBAR),
                     Column('name', column='icon')])

for icon, name in [(gtk.STOCK_OK, 'Apple'),
                   (gtk.STOCK_CANCEL, 'Pineapple'),
                   (gtk.STOCK_HELP, 'Kiwi'),
                   (gtk.STOCK_DELETE, 'Banana'),
                   (gtk.STOCK_HOME, 'Melon')]:
    fruits.append(Fruit(icon, name))

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_title('Fruits')
window.set_size_request(150, 180)

window.add(fruits)
window.show_all()

gtk.main()
