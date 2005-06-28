#!/usr/bin/env python
import sys
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi import set_decimal_separator
from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    A = 10.10

class EntryProxy(Proxy):
    widgets = [":A"]
    def __init__(self, model):
        self.set_numeric("A")
        self._build()
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Entry()
        self.win.add(self.A)

set_decimal_separator(",")
f = Foo()
c = EntryProxy(f)
assert c.A.get_text() == "10,1", c.A.get_text()
assert f.A == 10.1

set_decimal_separator("X")
f = Foo()
c = EntryProxy(f)
assert c.A.get_text() == "10X1", c.A.get_text()
assert f.A == 10.1

set_decimal_separator(".")
f = Foo()
c = EntryProxy(f)
assert c.A.get_text() == "10.1", c.A.get_text()
assert f.A == 10.1

set_decimal_separator("X")
f = Foo()
c = EntryProxy(f)
c.set_decimal_separator(".")
c.update("A") # Trigger view refresh
assert c.A.get_text() == "10.1", c.A.get_text()
assert f.A == 10.1

print "Separator OK"
