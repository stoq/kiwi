#!/usr/bin/env python
from sets import Set

import gtk

from kiwi.ui.views import BaseView
from kiwi.ui.widgets.combo import ProxyComboEntry


def load_colors():
    filename = "/usr/X11R6/etc/X11/rgb.txt"
    try:
        lines = file(filename).readlines()
    except IOError:
        return ['red', 'blue', 'yellow', 'green']

    # the first line we don't want
    lines = lines[1:]
    s = Set([c.strip().split('\t')[2] for c in lines])
    if '' in s:
        s.remove('')
    return list(s)


class Color:
    color = 'blue'


class FavouriteColor(BaseView):
    def __init__(self):
        win = gtk.Window()
        win.set_title("Silly question")
        win.set_border_width(12)
        label = gtk.Label("What is your favourite color?")
        box = gtk.VBox(spacing=6)
        box.pack_start(label, False)
        self.combo = ProxyComboEntry()
        self.combo.data_type = str
        self.combo.model_attribute = 'color'
        self.combo.prefill(load_colors(), sort=True)
        box.pack_start(self.combo, False)
        win.add(box)
        BaseView.__init__(self, toplevel=win,
                          delete_handler=self.quit_if_last)

the_color = Color()
app = FavouriteColor()
app.add_proxy(the_color, ['combo'])
app.show_all()
gtk.main()
print 'Your favourite color is', the_color.color
