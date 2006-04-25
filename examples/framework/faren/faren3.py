#!/usr/bin/env python
import gtk

from kiwi.ui.delegates import Delegate

class Farenheit(Delegate):
    widgets = ["quitbutton", "temperature", "celsius", "farenheit",
               "celsius_label" , "farenheit_label", "temperature_label"]
    gladefile = "faren"
    def __init__(self):
        Delegate.__init__(self, delete_handler=self.quit_if_last)

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
            try:
                farenheit, celsius = self.convert_temperature(float(temp))
            except ValueError:
                farenheit = celsius = float('nan')
            self.farenheit.set_text("%.2f" % farenheit)
            self.celsius.set_text("%.2f" % celsius)

delegate = Farenheit()
delegate.show()
gtk.main()
