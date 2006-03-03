import os
import sys
import time

try:
    import pygtk
    pygtk.require('2.0')
except:
    pass

import gtk

def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)

dir = os.path.dirname(__file__)
if not dir in sys.path:
    sys.path.insert(0, os.path.join(dir))

from kiwi.environ import environ
environ.add_resource('glade', dir)
