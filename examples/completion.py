# encoding: iso-8859-1
import gtk

from kiwi.ui.widgets.entry import ProxyEntry

def on_entry_activate(entry):
    print 'You selected:', entry.read()
    gtk.main_quit()

win = gtk.Window()
win.connect('delete-event', gtk.main_quit)

vbox = gtk.VBox()
win.add(vbox)

# Normal entry
entry = ProxyEntry()
entry.data_type = str
entry.connect('activate', on_entry_activate)
entry.prefill(['Belo Horizonte', u'São Carlos',
               u'São Paulo',  u'Båstad',
               u'Örnsköldsvik', 'sanca', 'sampa'])
vbox.pack_start(entry)

entry = ProxyEntry()
entry.data_type = int
entry.connect('activate', on_entry_activate)
entry.prefill([('Brazil', 186),
               ('Sweden', 9),
               ('China', 1306)])
vbox.pack_start(entry)

win.show_all()
gtk.main()
