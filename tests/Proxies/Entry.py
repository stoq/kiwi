#!/usr/bin/env python
import sys, pprint
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from mx import DateTime

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    A = "Alphabet"
    B = "Beetroot"
    C = 10
    D = 20
    E = DateTime.now()
    # F unset
    G = 30
    # H unset

class NumberFoo(Model):
    A = 1
    B = 2
    C = 3
    D = 4
    E = DateTime.now()
    # F unset
    G = 6
    # H unset

class EntryProxy(Proxy):
    widgets = [":B", ":A", ":C", ":D", ":E", ":F", ":G", ":H"]
    def __init__(self, model, flag=0):
        self._build()
        self.set_numeric("C")
        if flag:
            self.set_datetime("E")
        self.set_numeric("G")
        self.set_numeric("H")
        self.set_format("H", "%.3f")
        self.set_format("G", "%.3f")
        self.set_decimal_separator(",")
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Entry()
        self.B = gtk.Entry()
        self.C = gtk.Entry()
        self.D = gtk.Entry()
        self.E = gtk.Entry()
        self.F = gtk.Entry()
        self.F.set_text("NOOGIE")
        self.G = gtk.Entry()
        self.H = gtk.Entry()
        self.H.set_text("30.41")
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        vbox.add(self.G)
        vbox.add(self.H)
        self.vbox = vbox
        self.win.add(vbox)

class ComboProxy(EntryProxy):
    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Combo()
        self.A.set_popdown_strings(["foo"])
        self.B = gtk.Combo()
        self.B.set_popdown_strings(["bar"])
        self.C = gtk.Combo()
        self.C.set_popdown_strings(["99"])
        self.D = gtk.Combo()
        self.D.set_popdown_strings(["100"])
        self.E = gtk.Combo()
        self.F = gtk.Combo()
        self.F.entry.set_text("NOOGIE")
        self.G = gtk.Combo()
        self.H = gtk.Combo()
        self.H.entry.set_text("30.41")
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        vbox.add(self.G)
        vbox.add(self.H)
        self.win.add(vbox)

class LabelProxy(EntryProxy):
    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Label()
        self.B = gtk.Label()
        self.C = gtk.Label()
        self.D = gtk.Label()
        self.E = gtk.Label()
        self.F = gtk.Label("NOOGIE")
        self.G = gtk.Label()
        self.H = gtk.Label()
        self.H.set_text("30.41")
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        vbox.add(self.G)
        vbox.add(self.H)
        self.win.add(vbox)

class SpinProxy(EntryProxy):
    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.SpinButton(None, 1, 2)
        adj = self.A.get_adjustment()
        adj.step_increment = 1.0
        adj.changed()
        self.A.set_adjustment(adj)
        self.A.set_range(-100, 100)
        self.B = gtk.SpinButton(None, 1, 2)
        self.B.set_range(-100, 100)
        self.C = gtk.SpinButton(None, 1, 2)
        self.C.set_range(-100, 100)
        self.D = gtk.SpinButton(None, 1, 2)
        self.D.set_range(-100, 100)
        self.E = gtk.SpinButton(None, 1, 2)
        self.E.set_range(-100, 100)
        self.F = gtk.SpinButton(None, 1, 2)
        self.F.set_range(-100, 100)
        self.F.set_text("NOOGIE")
        self.G = gtk.SpinButton(None, 1, 2)
        self.G.set_range(-100, 100)
        self.H = gtk.SpinButton(None, 1, 2)
        self.H.set_range(-100, 100)
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        vbox.add(self.G)
        vbox.add(self.H)
        self.win.add(vbox)
        self.set_numeric(["A", "B", "C", "D", "E", "F"])

f = Foo()
try:
    c = EntryProxy(f)
except TypeError:
    pass
f.flush_proxies()
c = EntryProxy(f, 1)
assert f.A == "Alphabet", f.A
assert f.B == "Beetroot", f.B
assert f.C == 10, f.C
assert f.D == "20", f.D
assert f.F == "NOOGIE", f.F
assert f.H == 30.41, f.H
f.G = 30.42
c.A.set_text("Aspargus")
c.B.set_text("Barney")
c.C.set_text("200")
c.D.set_text("barney")
assert f.A == "Aspargus", f.A
assert f.B == "Barney", f.B
assert f.C == 200, f.D
assert f.D == "barney", f.D
t = c.G.get_text()
assert t == "30,420", t
assert f.G == 30.42
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
print "Entry OK"

f = Foo()
try:
    c = ComboProxy(f)
except TypeError:
    pass
f.flush_proxies()
c = ComboProxy(f, 1)
assert f.A == "Alphabet", f.A
assert f.B == "Beetroot", f.B
assert f.C == 10, f.C
assert f.D == "20", f.D
assert f.F == "NOOGIE", f.F
c.A.entry.set_text("Aspargus")
c.B.entry.set_text("Barney")
c.C.entry.set_text("200")
c.D.entry.set_text("barney")
f.G = 30.42
assert f.A == "Aspargus", f.A
assert f.B == "Barney", f.B
assert f.C == 200, f.D
assert f.D == "barney", f.D
t = c.G.entry.get_text()
assert t == "30,420", t
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
print "Combo OK"

f = Foo()
try:
    c = LabelProxy(f)
except TypeError:
    pass
f.flush_proxies()
c = LabelProxy(f, 1)
assert f.A == "Alphabet", f.A
assert f.B == "Beetroot", f.B
assert f.C == 10, f.C
# XXX: Label does *NOT* convert to text on startup because it never
# triggers signals - is this correct, and is Entry correct?
assert f.D == 20
# XXX: label doesn't generate signals, so we can't pick up the
# set_text() changes done to it. This is why
#   assert f.F == "NOOGIE"
# fails here. See WidgetProxies.Entry:Labelproxy.update for details.
f.A = "Aspargus"
f.B = "Barney"
try:
    f.C = "200"
except TypeError:
    f.C = 200
f.D = "barney"
f.G = 30.42
assert c.A.get() == "Aspargus", f.A
assert c.B.get() == "Barney", f.B
assert c.C.get() == "200", f.C
assert c.D.get() == "barney", f.D
t = c.G.get_text()
assert t == "30,420", t
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
print "Label OK"

f = NumberFoo()
assert f.D == 4, f.D
try:
    c = SpinProxy(f)
except TypeError:
    pass
f.flush_proxies()
c = SpinProxy(f, 1)
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
assert f.A == 0, f.A
assert f.B == 0, f.B
assert f.C == 0
assert f.D == 0, f.D
assert f.F == 0, f.F
c.A.set_text("4")
c.B.set_text("3")
c.C.set_text("2")
c.D.set_text("1")
f.G = 30.42
assert f.A == 4, f.A
assert f.B == 3, f.B
assert f.C == 2, f.D
assert f.D == 1, f.D
t = c.G.get_text()
assert t == "30,420", t
print "SpinButton OK"
