#!/usr/bin/env python
from kiwi import Views, Controllers
from kiwi.initgtk import gtk, quit_if_last

class FarenControl(Controllers.BaseController):
    def __init__(self, view):
        Controllers.BaseController.__init__(self, view)

    def on_quitbutton__clicked(self, *args):
        self.view.hide_and_quit()

    def after_temperature__changed(self, entry, *args):
        try:
            temp = float(entry.get_text())
        except ValueError:
            temp = 0
        celsius = (temp - 32) * 5/9.0
        farenheit = (temp * 9/5.0) + 32
        self.view.celsius.set_text("%.2f" % celsius)
        self.view.farenheit.set_text("%.2f" % farenheit)

widgets = ["quitbutton", "temperature", "celsius", "farenheit"]
view = Views.BaseView(gladefile="faren", delete_handler=quit_if_last,
                      widgets=widgets)
ctl = FarenControl(view)
view.show()
gtk.main()
