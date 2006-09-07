#!/usr/bin/env python
import gtk

from kiwi.controllers import BaseController
from kiwi.ui.views import BaseView
from kiwi.ui.gadgets import quit_if_last

class FarenControl(BaseController):

    def on_quitbutton__clicked(self, *args):
        self.view.hide_and_quit()

    def after_temperature__insert_text(self, entry, *args):
        try:
            temp = float(entry.get_text())
        except ValueError:
            temp = 0
        celsius = (temp - 32) * 5/9.0
        farenheit = (temp * 9/5.0) + 32
        self.view.celsius.set_text("%.2f" % celsius)
        self.view.farenheit.set_text("%.2f" % farenheit)

widgets = ["quitbutton", "temperature", "celsius", "farenheit"]
view = BaseView(gladefile="faren", delete_handler=quit_if_last,
                widgets=widgets)
ctl = FarenControl(view)
view.show()
gtk.main()
