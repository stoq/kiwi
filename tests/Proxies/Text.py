#!/usr/bin/env python
import sys, pprint
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from mx import DateTime

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.FrameWork import Model

class Foo(Model):
    A = "Alphabet"
    B = "Beetroot"
    C = 10
    D = 20
    E = DateTime.now()
    # F unset
    G = 30.42

class TextProxy(Proxy):
    widgets = [":A", ":B", ":C", ":D", ":E", ":F", ":G"]
    def __init__(self, model, flag=0):
        self._build()
        self.set_numeric("C")
        if flag:
            self.set_datetime("E")
        self.set_numeric("G")
        self.set_format("G", "%.3f")
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.GtkWindow()
        self.A = gtk.GtkText()
        self.A.set_editable(1)
        self.B = gtk.GtkText()
        self.B.set_editable(1)
        self.C = gtk.GtkText()
        self.C.set_editable(1)
        self.D = gtk.GtkText()
        self.D.set_editable(1)
        self.E = gtk.GtkText()
        self.E.set_editable(1)
        self.F = gtk.GtkText()
        self.F.set_editable(1)
        self.F.insert_text("NOOGIE")
        self.G = gtk.GtkText()
        self.G.set_editable(1)
        vbox = gtk.GtkVBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        vbox.add(self.G)
        self.win.add(vbox)

f = Foo()
try:
    c = TextProxy(f)
except TypeError:
    pass
f.flush_proxies()
assert f.A == "Alphabet", f.A
c = TextProxy(f, 1)
assert f.A == "Alphabet", f.A
assert f.B == "Beetroot", f.B
assert f.C == 10, f.C
assert f.D == "20", f.D
assert f.F == "NOOGIE", f.F
c.A.delete_text(0, c.A.get_length())
c.A.insert_text("Aspargus")
c.B.delete_text(0, c.B.get_length())
c.B.insert_text("Barney")
c.C.delete_text(0, c.C.get_length())
c.C.insert_text("200")
c.D.delete_text(0, c.D.get_length())
c.D.insert_text("barney")
f.G = 30.42
assert f.A == "Aspargus", f.A
assert f.B == "Barney", f.B
assert f.C == 200, f.D
assert f.D == "barney", f.D
t = c.G.get_chars(0, c.G.get_length())
assert t == "30.420", t
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
print "Text OK"
