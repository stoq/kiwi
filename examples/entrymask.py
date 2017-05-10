import sys

from gi.repository import Gtk

from kiwi.ui.entry import KiwiEntry


def main(args):
    w = Gtk.Window()
    w.set_position(Gtk.WindowPosition.CENTER)
    w.set_size_request(250, -1)
    w.set_title('ComboEntry example')
    w.connect('delete-event', Gtk.main_quit)

    e = KiwiEntry()
    e.set_mask('0000-00-00')
    w.add(e)

    w.show_all()
    e.set_position(0)
    Gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
