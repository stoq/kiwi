#!/usr/bin/env python

#
# Tests creating a Proxy against a widget that is not supported by
# Proxies (a Frame).
#

import sys
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model

class Foo(Model):
    pass

class NoProxy(Proxy):
    widgets = [":A"]
    def __init__(self, model, flag=0):
        self._build()
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)

    def _build(self):
        self.win = gtk.Window()
        self.A = gtk.Frame()
        self.win.add(self.A)

f = Foo()
try:
    c = NoProxy(f)
    raise AssertionError
except TypeError:
    print "None ok"
