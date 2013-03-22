import datetime
import gtk

from kiwi.currency import currency
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel

window = gtk.Window()
window.connect('delete-event', gtk.main_quit)
window.set_border_width(6)

vbox = gtk.VBox()
window.add(vbox)

data_types = [
    (True, bool),
    (42, int),
    (22.0 / 7.0, float),
    (3000L, long),
    ('THX', str),
    (datetime.datetime.now(), datetime.datetime),
    (datetime.date.today(), datetime.date),
    (datetime.time(11, 38, 00), datetime.time),
    (currency('50.1'), currency),
]

for data, data_type in data_types:
    hbox = gtk.HBox(True)
    vbox.pack_start(hbox, False, False, 6)

    label = ProxyLabel(data_type.__name__.capitalize())
    label.set_bold(True)
    hbox.pack_start(label)

    label = ProxyLabel(data_type=data_type)
    label.update(data)
    hbox.pack_start(label, False, False, 6)

    entry = ProxyEntry(data_type=data_type)
    entry.update(data)
    entry.validate()
    hbox.pack_start(entry, False, False, 6)

window.show_all()

gtk.main()
