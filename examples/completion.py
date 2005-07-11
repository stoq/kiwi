import gtk

from kiwi.ui.widgets.entry import Entry

entry = Entry()
entry.set_completion_strings(['apa', 'apapa', 'apbla',
                              'apppa', 'aaspa'])

win = gtk.Window()
win.connect('delete-event', gtk.main_quit)
win.add(entry)
win.show_all()

gtk.main()
