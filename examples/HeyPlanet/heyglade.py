#!/usr/bin/env python
import gtk

from kiwi.ui.gadgets import quit_if_last
from kiwi.ui.views import BaseView

app = BaseView(gladefile="hey", delete_handler=quit_if_last)
app.show()
gtk.main()
