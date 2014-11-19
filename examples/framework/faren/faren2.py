#!/usr/bin/env python
import gtk

from kiwi.controllers import BaseController
from kiwi.ui.views import BaseView


class FarenControl(BaseController):

    def convert_temperature(self, temp):
        celsius = (temp - 32) * 5 / 9.0
        farenheit = (temp * 9 / 5.0) + 32
        return farenheit, celsius

    def on_quitbutton__clicked(self, *args):
        self.view.hide_and_quit()

    # use changed instead of insert_text, since it catches deletes too
    def after_temperature__changed(self, entry, *args):
        temp = view.get_temp()
        if temp is None:
            self.view.clear_temp()
        else:
            farenheit, celsius = self.convert_temperature(float(temp))
            self.view.update_temp(farenheit, celsius)


class FarenView(BaseView):
    widgets = ["quitbutton", "temperature", "celsius", "farenheit",
               "celsius_label", "farenheit_label", "temperature_label"]

    def __init__(self):
        BaseView.__init__(self, gladefile="faren.ui",
                          delete_handler=self.quit_if_last)

    def get_temp(self):
        return self.temperature.get_text() or None

    def update_temp(self, farenheit, celsius):
        self.farenheit.set_text("%.2f" % farenheit)
        self.celsius.set_text("%.2f" % celsius)

    def clear_temp(self):
        self.farenheit.set_text("")
        self.celsius.set_text("")

view = FarenView()
ctl = FarenControl(view)
view.show()
gtk.main()
