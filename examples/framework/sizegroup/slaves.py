#!/usr/bin/env python
import gtk

from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate
from kiwi.ui.gadgets import quit_if_last


class NestedSlave(GladeSlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        GladeSlaveDelegate.__init__(self, gladefile="slave_view2.ui",
                                    toplevel_name="window_container")


# This slave will be attached to the toplevel view, and will contain another
# slave
class TestSlave(GladeSlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        # Be carefull that, when passing the widget list, the sizegroups
        # that you want to be merged are in the list, otherwise, they wont
        # be.
        GladeSlaveDelegate.__init__(self, gladefile="slave_view.ui",
                                    toplevel_name="window_container")

        self.slave = NestedSlave(self)
        self.attach_slave("eventbox", self.slave)
        self.slave.show()
        self.slave.focus_toplevel()  # Must be done after attach


class Shell(GladeDelegate):
    def __init__(self):
        GladeDelegate.__init__(self, gladefile="shell.ui",
                               delete_handler=quit_if_last)

        self.slave = TestSlave(self)
        self.attach_slave("placeholder", self.slave)
        self.slave.show()
        self.slave.focus_toplevel()  # Must be done after attach

    def on_ok__clicked(self, *args):
        self.hide_and_quit()

shell = Shell()
shell.show()

gtk.main()
