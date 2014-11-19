#!/usr/bin/env python
import gtk

from kiwi.ui.gadgets import quit_if_last
from kiwi.ui.views import BaseView

app = BaseView(gladefile="hey.ui",
               delete_handler=quit_if_last)

# the_label, a widget defined in glade, is
text = app.the_label.get_text()
# now an instance variable of the view
app.the_label.set_markup('<b>%s</b>' % text)
app.the_label.set_use_markup(True)
app.show()
gtk.main()
