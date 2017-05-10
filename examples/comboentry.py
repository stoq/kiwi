import sys

from gi.repository import Gtk

from kiwi.ui.comboentry import ComboEntry


def main(args):
    w = Gtk.Window()
    w.set_position(Gtk.WindowPosition.CENTER)
    w.set_size_request(250, -1)
    w.set_title('ComboEntry example')
    w.connect('delete-event', Gtk.main_quit)

    e = ComboEntry()
    e.prefill(['foo', 'bar', 'baz', 'biz', 'boz',
               'bsz', 'byz', 'kus', 'kaz', 'kes',
               'buz', 'bwq', 'uys'])
    w.add(e)

    w.show_all()
    Gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
