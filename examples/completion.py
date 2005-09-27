# encoding: iso-8859-1
import gtk

from kiwi.ui.widgets.entry import Entry

def on_entry_activate(entry):
    print 'You selected:', entry.read()
    gtk.main_quit()

win = gtk.Window()
win.connect('delete-event', gtk.main_quit)

vbox = gtk.VBox()
win.add(vbox)

# Normal entry
entry = Entry()
entry.connect('activate', on_entry_activate)
entry.set_completion_strings(['Belo Horizonte', u'São Carlos',
                              u'São Paulo',  u'Båstad',
                              u'Örnsköldsvik', 'sanca', 'sampa'])
vbox.pack_start(entry)


entry = Entry()
entry.connect('activate', on_entry_activate)
entry.set_completion_strings(['Brazil', 'Sweden', 'China'],
                             [186, 9, 1306])
entry.set_completion_strings()
vbox.pack_start(entry)

win.show_all()



gtk.main()
