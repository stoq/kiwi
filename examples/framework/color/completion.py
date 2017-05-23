import sys
from sets import Set

from gi.repository import Gtk

from kiwi.ui.entry import KiwiEntry
from kiwi.ui.entrycompletion import KiwiEntryCompletion


def load_colors():
    filename = "/usr/X11R6/etc/X11/rgb.txt"
    try:
        lines = open(filename).readlines()
    except IOError:
        return ['red', 'blue', 'yellow', 'green']

    # the first line we don't want
    lines = lines[1:]
    s = Set([c.strip().split('\t')[2] for c in lines])
    if '' in s:
        s.remove('')
    return list(s)


def main(args):
    w = Gtk.Window()
    w.set_position(Gtk.WindowPosition.CENTER)
    w.set_size_request(250, 300)
    w.set_title('KiwiEntryCompletion example')
    w.connect('delete-event', Gtk.main_quit)

    vbox = Gtk.VBox()
    w.add(vbox)

    model = Gtk.ListStore(str)
    list = sorted(load_colors())
    for i in list:
        model.append((i,))

    entry = KiwiEntry()
    vbox.pack_start(entry, False, True, 0)

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
    vbox.pack_start(sw, True, True, 0)

    treeview = Gtk.TreeView(model)
    treeview.append_column(
        Gtk.TreeViewColumn('Completions', Gtk.CellRendererText(), text=0))

    sw.add(treeview)

    completion = KiwiEntryCompletion()
    entry.set_completion(completion)
    completion.set_property('minimum-key-length', 0)
    completion.set_model(model)
    completion.set_treeview(treeview)

    w.show_all()
    Gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
