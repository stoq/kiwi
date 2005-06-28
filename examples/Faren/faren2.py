#!/usr/bin/env python
from kiwi import Views, Controllers
from kiwi.initgtk import gtk, quit_if_last

class FarenControl(Controllers.BaseController):
    def __init__(self, view):
        Controllers.BaseController.__init__(self, view)

    def convert_temperature(self, temp):
        celsius = (temp - 32) * 5/9.0
        farenheit = (temp * 9/5.0) + 32
        return farenheit, celsius

    def on_quitbutton__clicked(self, *args):
        self.view.hide_and_quit()

    # use changed instead of insert_text, since it catches deletes too
    def after_temperature__changed(self, entry, *args):
        temp = view.get_temp()
        if temp == None:
            self.view.clear_temp()
        else:
            farenheit, celsius = self.convert_temperature(float(temp))
            self.view.update_temp(farenheit, celsius)

class FarenView(Views.BaseView):
    widgets = ["quitbutton", "temperature", "celsius", "farenheit",
               "celsius_label" , "farenheit_label", "temperature_label"]
    def __init__(self):
        Views.BaseView.__init__(self, gladefile="faren",
                                delete_handler=quit_if_last)
        # Make labels bold
        self.temperature_label.set_markup("<b>%s</b>" % \
                                          self.temperature_label.get_text())
        self.farenheit_label.set_markup("<b>%s</b>" % \
                                        self.farenheit_label.get_text())
        self.celsius_label.set_markup("<b>%s</b>" % \
                                      self.celsius_label.get_text())

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
