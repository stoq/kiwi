#!/usr/bin/env python
import gtk

from kiwi.ui.gadgets import quit_if_last
from kiwi.ui.views import BaseView

class MyView(BaseView):
    gladefile = "hey"
    def __init__(self):
        BaseView.__init__(self, delete_handler=quit_if_last)
        text = self.the_label.get_text() # attached by constructor
        self.the_label.set_markup('<b>%s</b>' % text)
        self.the_label.set_use_markup(True)
        self.set_title("Avi's declaration") # change window title

app = MyView()
app.show()
gtk.main()
