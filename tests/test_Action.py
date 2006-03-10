#!/usr/bin/env python
from utils import refresh_gui
import unittest

from kiwi.ui.delegates import Delegate

class ActionDelegate(Delegate):
    def __init__(self):
        Delegate.__init__(self, gladefile="actions.glade",
                          toplevel_name='window1',
                           widgets=['New'],
                           delete_handler=self.quit_if_last)
        self.new_activated = False

    def on_New__activate(self, *args):
        self.new_activated = True

class ActionTest(unittest.TestCase):
    def testButtons(self):
        action_delegate = ActionDelegate()
        refresh_gui()
        action_delegate.New.activate()
        refresh_gui()
        self.assertEqual(action_delegate.new_activated, True)

if __name__ == '__main__':
    unittest.main()
