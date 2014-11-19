#!/usr/bin/env python
import unittest
import gtk

from kiwi.ui.delegates import Delegate, GladeDelegate
from utils import refresh_gui


class A:
    def on_foo__clicked(self, *args):
        self.x = "FOO in A"


class B:
    def on_foo__clicked(self, *args):
        self.x = "FOO in B"

    def on_bar__clicked(self, *args):
        self.y = "BAR in B"


class C:
    def on_foo__clicked(self, *args):
        self.x = "FOO in C"


class X(A, B, C):
    def on_foo__clicked(self, *args):
        self.x = "FOO in X"


class Y:
    def on_foo__clicked(self, *args):
        self.x = "FOO in Y"


class Foo(X, Y, Delegate):
    widget = ["foo"]

    def __init__(self):
        self.win = gtk.Window()
        self.foo = gtk.Button("CLICK ME AND BE HAPPY")
        self.bar = gtk.Button("CLICK ME AND BE HAPPY")
        v = gtk.VBox()
        v.add(self.foo)
        v.add(self.bar)
        self.win.add(v)
        self.x = self.y = "NOOO"
        Delegate.__init__(self, toplevel=self.win,
                          delete_handler=self.quit_if_last)

    def on_foo__clicked(self, *args):
        self.x = "FOO in Foo"

    def on_bar__clicked(self, *args):
        self.y = "BAR in B"


class ClickCounter(Delegate):
    """In this delegate we count the number of clicks we do"""
    def __init__(self):
        self.win = gtk.Window()
        self.button = gtk.Button('Click me!')
        self.win.add(self.button)
        Delegate.__init__(self, toplevel=self.win,
                          delete_handler=self.quit_if_last)

        self.clicks = 0

    def on_button__clicked(self, *args):
        self.clicks += 1


class GladeClickCounter(GladeDelegate):
    def __init__(self):
        GladeDelegate.__init__(self, gladefile="tests/simple_button",
                               domain='kiwi',
                               delete_handler=self.quit_if_last)

        self.clicks = 0

    def on_button__clicked(self, *args):
        self.clicks += 1


class DelegateTest(unittest.TestCase):
    def testButtons(self):
        f = Foo()
        refresh_gui()
        f.foo.clicked()
        refresh_gui()
        self.assertEqual(f.x, "FOO in Foo")
        f.bar.clicked()
        refresh_gui()
        self.assertEqual(f.y, "BAR in B")

    def testClickCounter(self):
        clickcounter = ClickCounter()
        refresh_gui()

        # one for the boys
        clickcounter.button.clicked()
        self.assertEqual(clickcounter.clicks, 1)

        # one for the girls
        clickcounter.button.clicked()
        self.assertEqual(clickcounter.clicks, 2)

    def testClickCounterGlade(self):
        clickcounter = GladeClickCounter()
        refresh_gui()

        # one for the boys
        clickcounter.button.clicked()
        self.assertEqual(clickcounter.clicks, 1)

        # one for the girls
        clickcounter.button.clicked()
        self.assertEqual(clickcounter.clicks, 2)

if __name__ == '__main__':
    unittest.main()
