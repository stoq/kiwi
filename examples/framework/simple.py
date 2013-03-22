#!/usr/bin/env python
import gtk

from kiwi.ui.delegates import Delegate


class Hello(Delegate):
    def __init__(self):
        self.index = 0
        self.text = ["I've decided to take my work back underground",
                     "To keep it from falling into the wrong hands."]

        topwidget = gtk.Window()
        topwidget.set_title("So...")
        self.button = gtk.Button(self.text[self.index])
        self.button.show()
        topwidget.add(self.button)

        Delegate.__init__(self, topwidget, delete_handler=gtk.main_quit)
        # focus button, our only widget
        self.focus_topmost()

    def on_button__clicked(self, button):
        self.index = self.index + 1

        # Two clicks and we're gone
        if self.index > 1:
            self.hide_and_quit()
            # the *handler's* return value disappears into GTK+
            return

        # update the label of the button
        button.set_label(self.text[self.index])

app = Hello()
app.show_and_loop()
