#!/usr/bin/env python
import sys
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    A = 1
    B = 0

class CheckProxy(Proxy):
    widgets = [":B", ":A"]
    def __init__(self, model):
        self._build()
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.CheckButton("This is A")
        self.B = gtk.CheckButton("This is B")
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        self.win.add(vbox)

class ToggleProxy(CheckProxy):
    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.ToggleButton("This is A")
        self.B = gtk.ToggleButton("This is B")
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        self.win.add(vbox)

f = Foo()
c = CheckProxy(f)
assert f.A == 1
assert f.B == 0
c.A.clicked()
c.B.clicked()
assert f.A == 0, f.A
assert f.B == 1, f.B
if DEBUG: c.show_all_and_loop() ; print f.__dict__
print "CheckButton OK"

f = Foo()
c = ToggleProxy(f)
assert f.A == 1, f.A
assert f.B == 0, f.B
c.A.clicked()
c.B.clicked()
assert f.A == 0, f.A
assert f.B == 1, f.B
if DEBUG: c.show_all_and_loop(); print f.__dict__
print "ToggleButton OK"
