import sys

import gtk

from kiwi.ui.comboentry import ComboEntry

def main(args):
    w = gtk.Window()
    w.set_position(gtk.WIN_POS_CENTER)
    w.set_size_request(250, -1)
    w.set_title('ComboEntry example')
    w.connect('delete-event', gtk.main_quit)

    e = ComboEntry()
    e.prefill(['foo', 'bar', 'baz', 'biz', 'boz',
               'bsz', 'byz', 'kus', 'kaz', 'kes',
               'buz', 'bwq', 'uys'])
    w.add(e)

    w.show_all()
    gtk.main()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
