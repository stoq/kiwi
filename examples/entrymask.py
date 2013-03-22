import sys

import gtk

from kiwi.ui.entry import KiwiEntry


def main(args):
    w = gtk.Window()
    w.set_position(gtk.WIN_POS_CENTER)
    w.set_size_request(250, -1)
    w.set_title('ComboEntry example')
    w.connect('delete-event', gtk.main_quit)

    e = KiwiEntry()
    e.set_mask('0000-00-00')
    w.add(e)

    w.show_all()
    e.set_position(0)
    gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
