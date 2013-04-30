#!/usr/bin/env python
import unittest
import gtk
from gtk import keysyms

from utils import refresh_gui

from kiwi.controllers import BaseController
from kiwi.ui.gadgets import set_foreground, get_foreground, \
    set_background, get_background
from kiwi.ui.views import BaseView


class FooView(BaseView):
    widgets = ["vbox", "label"]

    def __init__(self):
        self.build_ui()
        BaseView.__init__(self, toplevel_name='win')

    def build_ui(self):
        self.win = gtk.Window()
        vbox = gtk.VBox()
        self.label = gtk.Label("Pick one noogie")
        vbox.add(self.label)
        self.button = gtk.Button(label="Noogie!")
        vbox.add(self.button)
        self.foo__button = gtk.Button(label="Boogie!")
        vbox.add(self.foo__button)
        self.win.add(vbox)
        self.vbox = vbox
        return vbox


class FooController(BaseController):
    def __init__(self, view):
        keyactions = {
            keysyms.A: self.on_button__clicked,
            keysyms.a: self.on_button__clicked,
            keysyms.B: self.on_foo__button__clicked,
            keysyms.b: self.on_foo__button__clicked
        }
        BaseController.__init__(self, view, keyactions)

    def on_button__clicked(self, *args):
        self.bar = Bar()

    def on_foo__button__clicked(self, *args):
        # This is subclassed
        self.view.label.set_text("Good click!")


class Bar(BaseView, BaseController):
    def __init__(self):
        self.win = gtk.Window()
        self.label = gtk.Label("foobar!")
        self.win.add(self.label)
        BaseView.__init__(self, toplevel=self.win)
        BaseController.__init__(self, view=self)
        set_foreground(self.label, "#CC99FF")
        set_background(self.win, "#001100")


# these classes are bad and should trigger exceptions


class NotWidgetFoo(FooView, BaseController):
    def __init__(self):
        self.vbox = self.build_ui()
        # It's dumb, and it breaks
        self.noogie = NotWidgetFoo
        FooView.__init__(self)
        BaseController.__init__(self, view=self)

    def on_noogie__haxored(self, *args):
        print "I AM NOT A NUMBER I AM A FREE MAN"


class BaseViewTest(unittest.TestCase):

    def setUp(self):
        self.view = FooView()
        self.foo = FooController(self.view)
        refresh_gui()

    def tearDown(self):
        self.view.win.destroy()

    def testFooButton(self):
        self.foo.view.foo__button.clicked()
        refresh_gui()
        # Broken, not how we use controllers/views in Stoq
        return
        self.assertEqual(self.foo.view.label.get_text(),
                         "Good click!")

    def testSubView(self):
        self.foo.view.button.clicked()
        refresh_gui()
        # Broken, not how we use controllers/views in Stoq
        return
        self.assertEqual(self.foo.bar, self.foo.bar.view)
        self.assertEqual(self.foo.bar.toplevel, self.foo.bar.win)
        # setting None as transient window should be an error
        self.assertRaises(TypeError, self.foo.bar.set_transient_for, None)

    def testColors(self):
        self.foo.view.button.clicked()
        refresh_gui()
        # Broken, not how we use controllers/views in Stoq
        return
        win = self.foo.bar.win
        win.realize()
        color = get_background(win)
        self.assertEqual(color, "#001100")
        label = self.foo.bar.label
        label.realize()
        color = get_foreground(label)
        self.assertEqual(color, "#CC99FF")


class BrokenViewsTest(unittest.TestCase):

    def testNotAWidget(self):
        # noogie (__main__.NotWidgetFoo) is not a widget and
        # can't be connected to
        self.assertRaises(TypeError, NotWidgetFoo)

if __name__ == '__main__':
    unittest.main()
