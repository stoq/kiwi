#!/usr/bin/env python
from kiwi import Delegates
from kiwi.initgtk import gtk, quit_if_last

class Farenheit(Delegates.Delegate):
    widgets = ["quitbutton", "temperature", "celsius", "farenheit",
               "celsius_label" , "farenheit_label", "temperature_label"]
    def __init__(self):
        Delegates.Delegate.__init__(self, gladefile="faren", 
                                    delete_handler=quit_if_last)
        # Make labels bold
        self.temperature_label.set_markup("<b>%s</b>" % \
                                          self.temperature_label.get_text())
        self.farenheit_label.set_markup("<b>%s</b>" % \
                                        self.farenheit_label.get_text())
        self.celsius_label.set_markup("<b>%s</b>" % \
                                      self.celsius_label.get_text())
    
    def convert_temperature(self, temp):
        farenheit = (temp * 9/5.0) + 32
        celsius = (temp - 32) * 5/9.0
        return farenheit, celsius 
    
    def clear_temperature(self):
        self.farenheit.set_text("") 
        self.celsius.set_text("")

    # Signal handlers

    def on_quitbutton__clicked(self, *args):
        self.hide_and_quit()

    def after_temperature__changed(self, entry, *args):
        temp = entry.get_text().strip() or None
        if temp is None:
            self.clear_temperature()
        else:
            farenheit, celsius = self.convert_temperature(float(temp))
            self.farenheit.set_text("%.2f" % farenheit)
            self.celsius.set_text("%.2f" % celsius)

delegate = Farenheit()
delegate.show()
gtk.main()
