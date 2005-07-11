# encoding: iso-8859-1
import gtk

from kiwi.ui.widgets.entry import Entry

def on_entry_activate(entry):
    print 'You selected:', entry.get_text().encode('latin1')
    gtk.main_quit()

entry = Entry()
entry.connect('activate', on_entry_activate)
entry.set_completion_strings(['Belo Horizonte',
                              u'São Carlos',
                              u'São Paulo',
                              u'Båstad',
                              u'Örnsköldsvik',
                              'sanca',
                              'sampa'])

win = gtk.Window()
win.connect('delete-event', gtk.main_quit)
win.add(entry)
win.show_all()

gtk.main()
