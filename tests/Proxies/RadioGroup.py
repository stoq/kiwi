#!/usr/bin/env python
import sys, pprint
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    A = "Play"
    B = 222
    C = "OOH"
    # No D - Play
    E = None # Run
    # No F - Play

class RadioProxy(Proxy):
    def __init__(self, model):
        self._build()
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.Window()
        self.A1 = gtk.RadioButton(label="Play")
        self.A2 = gtk.RadioButton(self.A1, label="Hide")
        self.A3 = gtk.RadioButton(self.A1, label="Run")
        self.group_radiobuttons("A", ["A1", "A2", "A3"])

        self.B1 = gtk.RadioButton(label="B Play")
        self.B2 = gtk.RadioButton(self.B1, label="B Hide")
        self.B3 = gtk.RadioButton(self.B1, label="B Run")
        self.group_radiobuttons("B", {"B1": 111, "B2": 222, "B3": 333})

        self.C1 = gtk.RadioButton(label="C Play")
        self.C2 = gtk.RadioButton(self.C1, label="C Hide")
        self.C3 = gtk.RadioButton(self.C1, label="C Run")
        self.group_radiobuttons("C", {"C1": 111, "C2": 222, "C3": 333})

        self.D1 = gtk.RadioButton(label="D Play")
        self.D2 = gtk.RadioButton(self.D1, label="D Hide")
        self.D3 = gtk.RadioButton(self.D1, label="D Run")
        self.group_radiobuttons("D", {"D1": 111, "D2": 222, "D3": 333})

        self.E1 = gtk.RadioButton(label="E Play")
        self.E2 = gtk.RadioButton(self.E1, label="E Hide")
        self.E3 = gtk.RadioButton(self.E1, label="E Run")
        self.group_radiobuttons("E", {"E1": 111, "E2": 222, "E3": 333})

        vbox = gtk.VBox()
        vbox.add(self.A1)
        vbox.add(self.A2)
        vbox.add(self.A3)
        vbox.add(self.B1)
        vbox.add(self.B2)
        vbox.add(self.B3)
        vbox.add(self.C1)
        vbox.add(self.C2)
        vbox.add(self.C3)
        vbox.add(self.D1)
        vbox.add(self.D2)
        vbox.add(self.D3)
        vbox.add(self.E1)
        vbox.add(self.E2)
        vbox.add(self.E3)
        self.win.add(vbox)

f = Foo()
try:
    f.D
    raise AssertionError
except:
    pass
assert f.E == None, f.E
try:
    c = RadioProxy(f)
    raise AssertionError
except ValueError:
    pass
f.flush_proxies()
f.C = 333
c = RadioProxy(f)
assert f.A == "Play", f.A
assert f.B == 222, f.B
assert f.C == 333, f.C
assert f.D == 111, f.D
assert f.E == 111, f.E
c.A2.clicked()
c.B3.clicked()
c.C1.clicked()
assert f.A == "Hide", f.A
assert f.B == 333, f.B
assert f.C == 111, f.B
c.A3.clicked()
assert f.A == "Run", f.A
f.E = None
assert f.E == 111, f.E
if DEBUG: c.show_all_and_loop(); pprint.pprint(f.__dict__)
print 'RadioButton OK'
