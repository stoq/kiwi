import sys
from sets import Set

import gtk

from kiwi.ui.entry import KiwiEntry
from kiwi.ui.entrycompletion import KiwiEntryCompletion


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


def main(args):
    w = gtk.Window()
    w.set_position(gtk.WIN_POS_CENTER)
    w.set_size_request(250, 300)
    w.set_title('KiwiEntryCompletion example')
    w.connect('delete-event', gtk.main_quit)

    vbox = gtk.VBox()
    w.add(vbox)

    model = gtk.ListStore(str)
    list = load_colors()
    list.sort()
    for i in list:
        model.append((i,))

    entry = KiwiEntry()
    vbox.pack_start(entry, False)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
    vbox.pack_start(sw)

    treeview = gtk.TreeView(model)
    treeview.append_column(
        gtk.TreeViewColumn('Completions', gtk.CellRendererText(), text=0))

    sw.add(treeview)

    completion = KiwiEntryCompletion()
    entry.set_completion(completion)
    completion.set_property('minimum-key-length', 0)
    completion.set_model(model)
    completion.set_treeview(treeview)

    w.show_all()
    gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
