#!/usr/bin/env python
from gi.repository import Gtk

from kiwi.ui.views import BaseView


class HeyPlanet(BaseView):
    def __init__(self):
        win = Gtk.Window()
        win.set_title("I'm coming to London")
        label = Gtk.Label(label="Anything to declare?")
        win.add(label)
        win.set_default_size(200, 50)
        BaseView.__init__(self, toplevel=win,
                          delete_handler=self.quit_if_last)
app = HeyPlanet()
app.show_all()
Gtk.main()
