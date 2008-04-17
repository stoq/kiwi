# A simple example to demonstrate the ListDialog dialog

import gtk

from kiwi.enums import ListType
from kiwi.ui.listdialog import ListDialog
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.contextmenu import ContextMenu, ContextMenuItem

class Item(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class MyListDialog(ListDialog):

    columns = [Column('name')]
    list_type = ListType.UNEDITABLE


    def __init__(self):
        ListDialog.__init__(self)
        self._create_menu()

    def _create_menu(self):
        menu = ContextMenu()

        item = ContextMenuItem('_Foo', gtk.STOCK_COPY)
        item.connect('activate', self._on_foo_activate)
        item.connect('can-disable', self._on_foo_can_disable)
        menu.append(item)

        item = ContextMenuItem('Bar')
        item.connect('activate', self._on_bar_activate)
        menu.append(item)

        menu.append_separator()

        item = ContextMenuItem(gtk.STOCK_PASTE)
        item.connect('activate', self._on_paste_activate)
        menu.append(item)

        self.listcontainer.list.set_context_menu(menu)
        menu.show_all()

    def _on_foo_activate(self, menu_item):
        print 'foo'

    def _on_foo_can_disable(self, menu_item):
        return True

    def _on_bar_activate(self, menu_item):
        print 'bar'

    def _on_paste_activate(self, menu_item):
        print 'paste'

    def populate(self):
        return [Item('test')]

    def add_item(self):
        return Item("added")

dialog = MyListDialog()
dialog.run()


