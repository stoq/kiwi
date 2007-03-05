# A simple example to demonstrate the ListDialog dialog

from kiwi.enums import ListType
from kiwi.ui.listdialog import ListDialog
from kiwi.ui.objectlist import Column

class Item(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class MyListDialog(ListDialog):

    columns = [Column('name')]
    list_type = ListType.UNEDITABLE

    def populate(self):
        return [Item('test')]

    def add_item(self):
        return Item("added")

dialog = MyListDialog()
dialog.run()
