#!/usr/bin/env python
import sys, pprint
sys.path.insert(0, "../..")

DEBUG = 0
if len(sys.argv) > 1:
    DEBUG = 1

from Kiwi.initgtk import gtk
from Kiwi.Proxies import Proxy
from Kiwi.Models import Model
#from Kiwi.Menu import OptionMenu
from gtk import OptionMenu

def prefill(args):
    print "ARGS", args

class Foo(Model):
    A = "Run"
    B = "Hide"
    C = None # Play
    # No D - Play
    E = 666 # Run
    # No F - Play

class CheckProxy(Proxy):
    widgets = [":A", ":B", ":C", ":D", ":E", ":F"]
    def __init__(self, model):
        self._build()
        Proxy.__init__(self, model, delete_handler=gtk.mainquit)
        gtk.idle_add(self.focus_topmost)

    def _build(self):
        self.win = gtk.Window()
        self.A = OptionMenu()
        self.A.prefill(["Play", "Hide", "Run"])
        self.B = OptionMenu()
        self.B.prefill(["Play", "Hide", "Run"])
        self.C = OptionMenu()
        self.C.prefill(["Play", "Hide", "Run"])
        self.D = OptionMenu()
        self.D.prefill(["Play", "Hide", "Run"])
        self.E = OptionMenu()
        self.E.prefill([("Play", 111), ("Hide", 222) , ("Run", 666)])
        self.F = OptionMenu()
        self.F.prefill([("Play", 111), ("Hide", 222) , ("Run", 666)])
        vbox = gtk.VBox()
        vbox.add(self.A)
        vbox.add(self.B)
        vbox.add(self.C)
        vbox.add(self.D)
        vbox.add(self.E)
        vbox.add(self.F)
        self.win.add(vbox)

f = Foo()
c = CheckProxy(f)
assert f.A == "Run", f.A
assert f.B == "Hide", f.B
assert f.C == "Play", f.C
assert f.D == "Play", f.D
assert f.E == 666, f.E
assert f.F == 111, f.E
c.A.get_menu().children()[0].activate()
c.B.get_menu().children()[2].activate()
c.E.get_menu().children()[1].activate()
assert f.A == "Play", f.A
assert f.B == "Run", f.B
assert f.E == 222, f.B
try:
    f.E = 231
    raise AssertionError
except ValueError:
    # XXX: set value back to normal. See Model.__setattr__
    f.E = 222
if DEBUG: c.show_all_and_loop() ; pprint.pprint(f.__dict__)
print "OptionMenu OK"
