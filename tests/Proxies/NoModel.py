#!/usr/bin/env python

#
# Tests creating a Proxy with no initial model, and then adding one later
#

import sys, pprint
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    pass

class XProxy(Proxy):
    widgets = [":A"]
    def __init__(self, model=None, flag=0):
        self._build()
        self.set_numeric("A")
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        self.A.grab_focus()

    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Entry()
        self.win.add(self.A)

f = Foo()
c = XProxy()
c.new_model(f)
if DEBUG:
    c.show_all()
    gtk.mainloop()
    pprint.pprint(f.__dict__)
assert f.A == 0, f.A # XXX: Is this really expected?

f = Foo()
f.A = 10
c.new_model(f)
assert f.A == 10, f.A
t = c.A.get_text()
assert t == "10", t
print "NoModel ok"
