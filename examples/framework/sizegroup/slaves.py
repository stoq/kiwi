#!/usr/bin/env python
from gi.repository import Gtk

from kiwi.ui.delegates import GladeDelegate, GladeSubordinateDelegate
from kiwi.ui.gadgets import quit_if_last


class NestedSubordinate(GladeSubordinateDelegate):
    def __init__(self, parent):
        self.parent = parent
        GladeSubordinateDelegate.__init__(self, gladefile="subordinate_view2.ui",
                                    toplevel_name="window_container")


# This subordinate will be attached to the toplevel view, and will contain another
# subordinate
class TestSubordinate(GladeSubordinateDelegate):
    def __init__(self, parent):
        self.parent = parent
        # Be carefull that, when passing the widget list, the sizegroups
        # that you want to be merged are in the list, otherwise, they wont
        # be.
        GladeSubordinateDelegate.__init__(self, gladefile="subordinate_view.ui",
                                    toplevel_name="window_container")

        self.subordinate = NestedSubordinate(self)
        self.attach_subordinate("eventbox", self.subordinate)
        self.subordinate.show()
        self.subordinate.focus_toplevel()  # Must be done after attach


class Shell(GladeDelegate):
    def __init__(self):
        GladeDelegate.__init__(self, gladefile="shell.ui",
                               delete_handler=quit_if_last)

        self.subordinate = TestSubordinate(self)
        self.attach_subordinate("placeholder", self.subordinate)
        self.subordinate.show()
        self.subordinate.focus_toplevel()  # Must be done after attach

    def on_ok__clicked(self, *args):
        self.hide_and_quit()

shell = Shell()
shell.show()

Gtk.main()
